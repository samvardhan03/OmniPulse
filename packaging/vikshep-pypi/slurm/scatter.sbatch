#!/bin/bash
#SBATCH --job-name=vikshep-scatter
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00

module load cuda/12.4
source "$HOME/vikshep-venv/bin/activate"

export OMNIPULSE_MCP_BIN="$HOME/omnipulse-rs/target/release/omnipulse-mcp"

python -m vikshep_ingest.serve --shm-dir "$TMPDIR/shm" &
bun run "$HOME/Vikshep/agent/src/main.ts" process \
    --input "$DATA/jets.root" \
    --request "tag jets, decorrelate mass"
