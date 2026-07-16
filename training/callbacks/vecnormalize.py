from __future__ import annotations

from pathlib import Path

from stable_baselines3.common.callbacks import BaseCallback


class SaveVecNormalizeCallback(BaseCallback):
    """Save training observation statistics when a new best model is found."""

    def __init__(self, save_path: Path, verbose: int = 0) -> None:
        super().__init__(verbose=verbose)
        self.save_path = save_path

    def _on_step(self) -> bool:
        vec_normalize = self.model.get_vec_normalize_env()
        if vec_normalize is None:
            raise RuntimeError(
                "VecNormalize statistics were requested, but the model environment "
                "is not normalized."
            )
        vec_normalize.save(self.save_path)
        if self.verbose:
            print(f"Saved VecNormalize statistics: {self.save_path}")
        return True
