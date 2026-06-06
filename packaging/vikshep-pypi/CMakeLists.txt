cmake_minimum_required(VERSION 3.18)
project(vikshep LANGUAGES CXX)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)
find_package(CUDAToolkit QUIET)

set(CMAKE_CXX_STANDARD 17)

# ---------------------------------------------------------------------------
# Locate omni-wst-core/cpp — works both in the dataplane-contrib overlay
# (pre-merge) and after the overlay has been rsync'd into the OmniPulse
# monorepo root (post-merge).
#
#   Pre-merge layout:  dataplane-contrib/packaging/vikshep-pypi/  →  ../omni-wst-core/cpp
#   Post-merge layout: packaging/vikshep-pypi/                    →  ../../omni-wst-core/cpp
# ---------------------------------------------------------------------------
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../omni-wst-core/cpp/scatter_engine.cuh")
    set(WST_CORE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../omni-wst-core/cpp")
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../omni-wst-core/cpp/scatter_engine.cuh")
    set(WST_CORE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../omni-wst-core/cpp")
else()
    message(FATAL_ERROR
        "omni-wst-core/cpp not found relative to ${CMAKE_CURRENT_SOURCE_DIR}.\n"
        "Expected at ../omni-wst-core/cpp (pre-merge overlay) or "
        "../../omni-wst-core/cpp (post-merge monorepo).")
endif()
message(STATUS "WST_CORE_ROOT = ${WST_CORE_ROOT}")

if(CUDAToolkit_FOUND)
    enable_language(CUDA)
    set(CMAKE_CUDA_STANDARD 17)

    # Default to Ampere + Hopper + Blackwell; override with -DCMAKE_CUDA_ARCHITECTURES=native
    if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
        set(CMAKE_CUDA_ARCHITECTURES 80 90 100)
    endif()

    set(SCATTER_SOURCES
        ${WST_CORE_ROOT}/scatter_bridge.cpp
        ${WST_CORE_ROOT}/scatter.cu
        ${WST_CORE_ROOT}/filter_bank.cu
        ${CMAKE_CURRENT_SOURCE_DIR}/cpp/vikshep_bindings.cpp
    )

    pybind11_add_module(_scatter MODULE ${SCATTER_SOURCES})

    target_include_directories(_scatter PRIVATE
        ${WST_CORE_ROOT}
        ${CMAKE_CURRENT_SOURCE_DIR}/cpp
    )

    target_link_libraries(_scatter PRIVATE
        CUDA::cudart
        CUDA::cufft
    )

    target_compile_options(_scatter PRIVATE
        $<$<COMPILE_LANGUAGE:CUDA>:
            --expt-relaxed-constexpr
            -O3
            --use_fast_math
            -gencode arch=compute_80,code=sm_80
            -gencode arch=compute_90,code=sm_90
            -gencode arch=compute_100,code=sm_100
        >
        $<$<COMPILE_LANGUAGE:CXX>:-O3>
    )

    # Required so scatter.cu / filter_bank.cu can be linked with the pybind module
    set_target_properties(_scatter PROPERTIES CUDA_SEPARABLE_COMPILATION ON)

    install(TARGETS _scatter DESTINATION vikshep)

else()
    message(STATUS
        "CUDAToolkit not found — vikshep installs as a pure-Python stub. "
        "On EDDIE: module load cuda/12.4 && pip install -e . --no-build-isolation")

    # Write a sentinel so __init__.py can detect non-CUDA builds cleanly.
    file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/_no_cuda.py"
         "# vikshep CUDA extension not built on this host\n")
    install(FILES "${CMAKE_CURRENT_BINARY_DIR}/_no_cuda.py" DESTINATION vikshep)
endif()
