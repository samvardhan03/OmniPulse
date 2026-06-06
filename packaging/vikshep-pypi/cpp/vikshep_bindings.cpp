// vikshep_bindings.cpp — pybind11 wrapper for the n-D scattering engine.
//
// Only compiled when CUDAToolkit is present (CMakeLists.txt guards this).
// run_scattering / free_scatter_result are defined in scatter_bridge.cpp.

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "scatter_engine.cuh"   // ScatterResult struct + group tags

#include <cmath>
#include <cstring>
#include <stdexcept>
#include <string>

namespace py = pybind11;

// C-linkage entry points from scatter_bridge.cpp
extern "C" {
    ScatterResult run_scattering(
        uint64_t host_ptr, int numel, int dim, int group,
        int J, int Q, int L, int depth, int N_axis);
    void free_scatter_result(ScatterResult r);
}

// Map Python group string to the integer codes defined in scatter_bridge.cpp
static int group_code(const std::string& g) {
    if (g == "trivial") return 0;  // TRIVIAL
    if (g == "so2")     return 1;  // SO2_G
    if (g == "so3")     return 2;  // SO3_G
    throw std::invalid_argument("unknown group '" + g + "'; expected trivial|so2|so3");
}

static py::array_t<float> scattering_fn(
    py::array_t<float, py::array::c_style | py::array::forcecast> arr,
    int                dim,
    const std::string& group,
    int                J,
    int                Q,
    int                L,
    int                order
) {
    py::buffer_info buf = arr.request();
    int numel  = static_cast<int>(buf.size);
    // N_axis: side length — must satisfy N_axis^dim ≈ numel (matches scattering.rs)
    int N_axis = static_cast<int>(std::round(std::pow(static_cast<double>(numel), 1.0 / dim)));
    int grp    = group_code(group);

    ScatterResult r = run_scattering(
        reinterpret_cast<uint64_t>(buf.ptr),
        numel, dim, grp, J, Q, L, order, N_axis
    );

    if (r.coeff_ptr == 0)
        throw std::runtime_error("run_scattering returned null coeff_ptr");

    py::array_t<float> out({static_cast<py::ssize_t>(r.coeff_count)});
    std::memcpy(out.mutable_data(),
                reinterpret_cast<const void*>(r.coeff_ptr),
                r.coeff_count * sizeof(float));
    free_scatter_result(r);
    return out;
}

PYBIND11_MODULE(_scatter, m) {
    m.doc() = "vikshep n-D / SE(2) / SO(3) wavelet scattering (CUDA-accelerated)";
    m.def("scattering", &scattering_fn,
          py::arg("arr"),
          py::arg("dim"),
          py::arg("group"),
          py::arg("J"),
          py::arg("Q"),
          py::arg("L"),
          py::arg("order") = 2,
          "Compute n-D wavelet scattering on a float32 C-contiguous array.\n\n"
          "Returns a 1-D float32 array of scattering coefficients.");
}
