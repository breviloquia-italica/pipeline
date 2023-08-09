#!/usr/bin/env bash

set -o nounset

module purge
module load "$HPC_PYMD"

source "$HPC_VENV"/bin/activate

function ask {
        dialog --output-fd 1 --title "JupyterLab x SLURM" --inputbox "$1" 8 30 "$2"
}

ACCOUNT=$(ask "Account:" standard);
PARTITION=$(ask "Partition:" cpu-intel-01)
CPU=$(ask "Cores:" 28)
MEM=$(ask "Memory:" 128GB)
TIME=$(ask "Time:" 8:00:00)
PORT=$(ask "Port:" 8888)

tmux new-session \
srun \
        --job-name=jupyter \
        --nodes=1 \
        --ntasks-per-node=1 \
        --cpus-per-task="$CPU" \
        --hint=nomultithread \
        --mem="$MEM" \
        --account="$ACCOUNT" \
        --partition="$PARTITION" \
        --time="$TIME" \
        --pty \
        --chdir "$HPC_PATH" \
jupyter-lab \
        --no-browser \
        --ip=0.0.0.0 \
        --port="$PORT"

deactivate

module purge

clear
