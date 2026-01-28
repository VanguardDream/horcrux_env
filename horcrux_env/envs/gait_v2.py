from typing import Optional
import numpy as np

class GaitV2():
    """
    GaitV2 class is a gait generator for the snake robot.
    It generates the gait pattern based on the parameters.
    params: tuple[
        float,  # e_d1: dorsal spatial parameter
        float,  # e_l1: lateral spatial parameter
        int,    # e_d2: dorsal temporal parameter
        int,    # e_l2: lateral temporal parameter
        float,  # delta: phase difference (deg)
        int     # reverse flag (>0: forward, <0: backward)
    ]
    sampling_t: float = 0.1
    model_timestep: float = 0.005
    frame_skip: int = 20
    """
    def __init__(self, params:tuple[float, float, int, int, float, int], sampling_t = 0.1, model_timestep = 0.005, frame_skip = 20) -> None:
        self.model_timestep = model_timestep
        self.frame_skip = frame_skip
        self.gait_sampling_interval = model_timestep * frame_skip

        self._ed1 = params[0]
        self._ed2 = params[2]
        self._el1 = params[1]
        self._el2 = params[3]
        self._delta = params[4]

        self._reverse = False
        if len(params) > 5:
            if params[5] > 0:
                self._reverse = False
            else:
                self._reverse = True

        self._t = np.arange(0, 2000 * np.pi * (1 / np.gcd(self._ed2, self._el2)), self.gait_sampling_interval).transpose()

        self.MotionMatrix = self.getMotionMat().copy()
        self.joints = self.MotionMatrix.shape[0]
        self.Mvecs = self.MotionMatrix.shape[1]

    def getMotionMat(self)->np.ndarray:
        raw_serp = self.serpenoid(self._t, self._ed1, self._el1, self._ed2, self._el2, self._delta)
        M_mat = self.__genMotionMat(raw_serp)

        return M_mat
    
    def getMvec(self, k):
        if self._reverse:
            k = -k
            
        k = k % self.Mvecs

        return self.MotionMatrix[:,k]
    
    def reset(self, params: Optional[tuple[float, float, int, int, float, int]] = None, 
              model_timestep: Optional[float] = None, 
              frame_skip: Optional[int] = None):
        """
        Reset the gait generator to initial state.
        Optionally update parameters before regenerating the time array and motion matrix.
        
        Args:
            params: Optional tuple of gait parameters (e_d1, e_l1, e_d2, e_l2, delta, reverse_flag).
                    If provided, updates the gait parameters.
            model_timestep: Optional model timestep. If provided, updates model_timestep.
            frame_skip: Optional frame skip value. If provided, updates frame_skip.
        """
        # Update gait parameters if provided
        if params is not None:
            self._ed1 = params[0]
            self._ed2 = params[2]
            self._el1 = params[1]
            self._el2 = params[3]
            self._delta = params[4]
            
            self._reverse = False
            if len(params) > 5:
                if params[5] > 0:
                    self._reverse = False
                else:
                    self._reverse = True
        
        # Update sampling parameters if provided
        if model_timestep is not None:
            self.model_timestep = model_timestep
        
        if frame_skip is not None:
            self.frame_skip = frame_skip
        
        # Recalculate gait sampling interval
        self.gait_sampling_interval = self.model_timestep * self.frame_skip
        
        # Regenerate time array and motion matrix
        self._t = np.arange(0, 2000 * np.pi * (1 / np.gcd(self._ed2, self._el2)), self.gait_sampling_interval).transpose()
        self.MotionMatrix = self.getMotionMat().copy()
        self.joints = self.MotionMatrix.shape[0]
        self.Mvecs = self.MotionMatrix.shape[1]
        
    ## Predefined functions
    def serpenoid(self, t, e_d1:float, e_l1:float, e_d2:float, e_l2:float, delta:float)->np.ndarray:
        #Hirose (1993) serpenoid curve implementations
        e_d1 = np.radians(e_d1)
        e_l1 = np.radians(e_l1)
        delta = np.radians(delta)

        f1 = (e_d2/10) * t
        f2 = (e_l2/10) * t

        j_1 = np.sin(e_d1 + f1)
        j_2 = np.sin(e_l1 * 2 + f2 + delta)

        j_3 = np.sin(e_d1 * 3 + f1)
        j_4 = np.sin(e_l1 * 4 + f2 + delta)

        j_5 = np.sin(e_d1 * 5 + f1)
        j_6 = np.sin(e_l1 * 6 + f2 + delta)

        j_7 = np.sin(e_d1 * 7 + f1)
        j_8 = np.sin(e_l1 * 8 + f2 + delta)

        j_9 = np.sin(e_d1 * 9 + f1)
        j_10 = np.sin(e_l1 * 10 + f2 + delta)

        j_11 = np.sin(e_d1 * 11 + f1)
        j_12 = np.sin(e_l1 * 12 + f2 + delta)

        j_13 = np.sin(e_d1 * 13 + f1)
        j_14 = np.sin(e_l1 * 14 + f2 + delta)

        return np.array([j_1, j_2, j_3, j_4, j_5, j_6, j_7, j_8, j_9, j_10, j_11, j_12, j_13, j_14])

    def __genMotionMat(self, serp_pos : np.array)->np.ndarray:
        serp_vel = np.diff(serp_pos.copy()) * (1 / self.gait_sampling_interval)
        serp_tor = np.diff(serp_vel.copy()) * (1 / self.gait_sampling_interval)

        motionMat = np.sign(serp_tor).copy()

        return motionMat