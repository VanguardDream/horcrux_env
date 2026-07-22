from typing import Dict, Optional, Tuple, Union
from horcrux_env.envs.gait_v2 import GaitV2

import importlib.resources as resources
import numpy as np

from gymnasium import utils
from gymnasium.envs.mujoco import MujocoEnv
from gymnasium.spaces import Box

from scipy.spatial.transform import Rotation

from collections import deque

DEFAULT_CAMERA_CONFIG = {}

__mjcf_model_path__ = str(resources.files("horcrux_env.resources") / "horcrux_plane.xml")

# __mjcf_model_path__ = 'horcrux_plane.xml'

class MovingAverageFilter1D:
    def __init__(self, window_size=20):
        self.window_size = window_size
        self.x_queue = deque(maxlen=window_size)

    def update(self, new_x):
        self.x_queue.append(new_x)

        avg_x = np.mean(self.x_queue) if self.x_queue else 0.0

        return avg_x
    
    def reset(self, window_size=20):
        if(self.x_queue.maxlen != window_size):
            del self.x_queue
            self.x_queue = deque(maxlen=window_size)
            self.x_queue.clear()
        else:
            self.x_queue.clear()
        

class MovingAverageFilter3D:
    def __init__(self, window_size=20):
        self.window_size = window_size
        self.x_queue = deque(maxlen=window_size)
        self.y_queue = deque(maxlen=window_size)
        self.z_queue = deque(maxlen=window_size)

    def update(self, new_x, new_y, new_z):
        self.x_queue.append(new_x)
        self.y_queue.append(new_y)
        self.z_queue.append(new_z)

        avg_x = np.mean(self.x_queue) if self.x_queue else 0.0
        avg_y = np.mean(self.y_queue) if self.y_queue else 0.0
        avg_z = np.mean(self.z_queue) if self.z_queue else 0.0

        return avg_x, avg_y, avg_z
    
    def reset(self, window_size=20):
        if(self.x_queue.maxlen != window_size):
            del self.x_queue
            del self.y_queue
            del self.z_queue

            self.x_queue = deque(maxlen=window_size)
            self.y_queue = deque(maxlen=window_size)
            self.z_queue = deque(maxlen=window_size)

            self.x_queue.clear()
            self.y_queue.clear()
            self.z_queue.clear()
        else:
            self.x_queue.clear()
            self.y_queue.clear()
            self.z_queue.clear()

class MovingAverageFilterQuaternion:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.w_queue = deque(maxlen=window_size)
        self.x_queue = deque(maxlen=window_size)
        self.y_queue = deque(maxlen=window_size)
        self.z_queue = deque(maxlen=window_size)

    def update(self, quat):
        if not (np.linalg.norm(quat) < 1e-8):
            self.w_queue.append(quat[0])
            self.x_queue.append(quat[1])
            self.y_queue.append(quat[2])
            self.z_queue.append(quat[3])
        else:
            self.w_queue.append(1)
            self.x_queue.append(0)
            self.y_queue.append(0)
            self.z_queue.append(0)

        _raw_quat = np.array([self.w_queue, self.x_queue, self.y_queue, self.z_queue]).T

        _rot = Rotation.from_quat(_raw_quat, scalar_first=True)

        _avg_rot = _rot.mean().as_quat(scalar_first=True)

        return _avg_rot
    
    def reset(self, window_size=10):
        if(self.w_queue.maxlen != window_size):
            del self.w_queue
            del self.x_queue
            del self.y_queue
            del self.z_queue

            self.w_queue = deque(maxlen=window_size)
            self.x_queue = deque(maxlen=window_size)
            self.y_queue = deque(maxlen=window_size)
            self.z_queue = deque(maxlen=window_size)

            self.w_queue.clear()
            self.x_queue.clear()
            self.y_queue.clear()
            self.z_queue.clear()
        else:
            self.w_queue.clear()
            self.x_queue.clear()
            self.y_queue.clear()
            self.z_queue.clear()

# class MovingAverageFilterQuaternion:
#     def __init__(self, window_size=10):
#         self.window_size = window_size
#         self.quat_queue = deque(maxlen=window_size)  # (x, y, z, w) 형식

#     def update(self, new_quat):  # new_quat: (x, y, z, w) or (4,) ndarray
#         # 부호 일관성 유지
#         if not (np.linalg.norm(new_quat) < 1e-8):
#             if self.quat_queue:
#                 last_quat = self.quat_queue[-1]
#                 if np.dot(last_quat, new_quat) < 0:
#                     new_quat = -new_quat

#             self.quat_queue.append(new_quat)
#         else:
#             self.quat_queue.append(np.array([1, 0, 0, 0]))

#         if len(self.quat_queue) < 2:
#             return Rotation.from_quat(self.quat_queue[-1], scalar_first=True).as_quat(scalar_first=True)  # 초기값은 그대로 반환

#         # 고유값 기반 평균
#         A = np.zeros((4, 4))
#         for q in self.quat_queue:
#             q = q / np.linalg.norm(q)
#             A += np.outer(q, q)
#         A /= len(self.quat_queue)

#         eigvals, eigvecs = np.linalg.eigh(A)
#         avg_quat = eigvecs[:, np.argmax(eigvals)]  # 최대 고유값의 고유벡터

#         if avg_quat[3] < 0:  # w<0이면 부호 반전
#             avg_quat = -avg_quat

#         # scipy는 (x, y, z, w) 형식 사용
#         rot_avg = Rotation.from_quat(avg_quat, scalar_first=True)

#         # print("Quaternion sequence (Euler angles):")
#         for q in self.quat_queue:
#             # print(R.from_quat(q).as_euler('XYZ', degrees=True))
#             pass

#         # print("Averaged (Euler):", rot_avg.as_euler('XYZ', degrees=True))

#         return rot_avg.as_quat(scalar_first=True)


class PlaneJoyDirWorld(MujocoEnv, utils.EzPickle):
    metadata = {
        "render_modes": [
            "human",
            "rgb_array",
            "depth_array",
        ],
    }
    def __init__(
            self, 
            model_path = __mjcf_model_path__,
            frame_skip: int = 10, 
            gait_sampling_interval: float = 0.05,
            default_camera_config: Dict[str, Union[float, int]] = DEFAULT_CAMERA_CONFIG,
            forward_reward_weight: float = 60,
            rotation_reward_weight: float = 45,
            termination_reward: float = 0,
            side_cost_weight:float = 60,
            ctrl_cost_weight: float = 0,
            proj_dist_cost_weight: float = 0,
            rotation_norm_cost_weight: float = 0.5,
            rotation_orientation_cost_weight: float = 0.05,
            unhealthy_cost_weight: float = 2,
            efficiency_reward_weight: float = 3,
            healthy_reward: float = 2,
            main_body: Union[int, str] = 2,
            render_camera_name = "ceiling",
            terminate_when_unhealthy: bool = True,
            unhealthy_max_steps: int = 30,
            healthy_roll_range: Tuple[float, float] = (-45, 45),
            terminating_roll_range: Tuple[float, float] = (-120, 120),
            contact_force_range: Tuple[float, float] = (-1.0, 1.0),
            reset_noise_scale: float = 0.1,
            use_gait: bool = True,
            use_friction_chg: bool = False,
            joy_input_random: bool = True,
            joy_input: Union[float, float, float] = (1, 0, 0), # X axis velocity, Y axis velocity, Yaw angular velocity
            gait_params: Tuple[float, float, float, float, float] = (30, 30, 40, 40, 23),
            use_imu_window: bool = False,
            use_vels_window: bool = False,
            **kwargs,
    ):
        utils.EzPickle.__init__(
            self,
            model_path,
            frame_skip,
            gait_sampling_interval,
            default_camera_config,
            forward_reward_weight,
            rotation_reward_weight,
            termination_reward,
            side_cost_weight,
            ctrl_cost_weight,
            proj_dist_cost_weight,
            rotation_norm_cost_weight,
            unhealthy_cost_weight,
            healthy_reward,
            main_body,
            render_camera_name,
            terminate_when_unhealthy,
            unhealthy_max_steps,
            healthy_roll_range,
            terminating_roll_range,
            contact_force_range,
            reset_noise_scale,
            use_gait,
            use_friction_chg,
            joy_input_random,
            joy_input,
            gait_params,
            use_imu_window,
            use_vels_window,
            **kwargs,                
        )
        self._gait_sampling_interval = gait_sampling_interval
        self._forward_reward_weight = forward_reward_weight
        self._rotation_reward_weight = rotation_reward_weight
        self.termination_reward = termination_reward
        self._side_cost_weight = side_cost_weight
        self._ctrl_cost_weight = ctrl_cost_weight
        self._proj_dist_cost_weight = proj_dist_cost_weight
        self._rotation_norm_cost_weight = rotation_norm_cost_weight
        self._rotation_orientation_cost_weight = rotation_orientation_cost_weight
        self._unhealthy_cost_weight = unhealthy_cost_weight
        self._efficiency_reward_weight = efficiency_reward_weight
        self._healthy_reward = healthy_reward
        self._healthy_roll_range = healthy_roll_range
        self._terminating_roll_range = terminating_roll_range
        self._contact_force_range = contact_force_range
        self._reset_noise_scale = reset_noise_scale
        self._main_body = main_body
        self._terminate_when_unhealthy = terminate_when_unhealthy
        self._use_gait = use_gait
        self._use_friction_chg = use_friction_chg
        self._gait_params = gait_params
        self._k = 0
        self._unhealthy_max_steps = unhealthy_max_steps
        self._unhealth_steps = 0
        self._robot_body_names = ["link1","link2","link3","link4","link5","link6","link7","link8","link9","link10","link11","link12","link13","link14","link15"]
        self._n_step = 0
        self._initial_com = np.array([0,0,0])
        self._initial_rpy = np.array([0,0,0])
        self._initial_head_rpy = np.array([0,0,0])
        self._cur_euler_ypr = np.array([0,0,0])
        self._joy_input = np.array(joy_input)
        self._joy_input_random = joy_input_random
        self._use_imu_mov_mean = use_imu_window
        self._use_vels_mov_mean = use_vels_window
        self._friction_information = [0, 0, 0]

        MujocoEnv.__init__(
                self,
                model_path,
                frame_skip,
                width=1280,
                height=720,
                observation_space = None, # define later
                default_camera_config = default_camera_config,
                camera_name = render_camera_name,
                **kwargs,
        )

        _temporal_param = max(self._gait_params[2], self._gait_params[3])
        _period = int(( (2 * np.pi) / (_temporal_param / 10) ) * ( 1 / (self.model.opt.timestep * self.frame_skip) ) )  # 좌변 -> 초 단위, 우변 -> 초 단위를 몇 슬롯으로 나눌지
        _period2 = int(( 1 / (self.model.opt.timestep * self.frame_skip) ) * 0.15)

        self._mov_mean_vels = MovingAverageFilter3D(window_size=_period)
        # self._mov_gait_ypr = MovingAverageFilter3D(window_size=_period * 2)
        self._mov_gait_ypr = MovingAverageFilterQuaternion(window_size=_period * 2)

        # IMU data filter
        self._mov_mean_imu_vel = MovingAverageFilter3D(window_size=_period2)
        self._mov_mean_imu_acc = MovingAverageFilter3D(window_size=_period2)
        self._mov_mean_imu_quat = MovingAverageFilterQuaternion(window_size=_period2)
        self._mov_vel_orient = MovingAverageFilter1D(window_size=_period2)

        self._gait = GaitV2(gait_params, sampling_t = gait_sampling_interval, frame_skip=self.frame_skip)

        self.metadata = {
            "render_modes": [
                "human",
                "rgb_array",
                "depth_array",
            ],
            "render_fps": int(np.round(1.0 / self.dt)),
        }

        obs_size = self.data.sensordata.size + 14 + 3 ## Motion vector + Joy input

        self.observation_space = Box(
                low=-np.inf, high= np.inf, shape=(obs_size,)
        )

        self.action_space = Box(
                low=0, high=2.7, shape=(14,)
        )

        self._motion_vector = np.array([0] * 14)
        self.observation_structure = {
                "jpos":self.data.sensordata[:14], #14
                "jvel":self.data.sensordata[14:28], #14
                "jtor":self.data.sensordata[28:42], #14
                "link_contacts_top":self.data.sensordata[42:56], #14
                "link_contacts_bot":self.data.sensordata[56:70], #14
                "head_orientation":self.data.sensordata[70:74], #4
                "head_angvel":self.data.sensordata[74:77], #3
                "head_linacc":self.data.sensordata[77:80], #3
                "motion_vector":self._motion_vector, #14
                "joy_input":self._joy_input, #3
        }

    @property
    def healthy_reward(self):          
            return self.is_healthy * self._healthy_reward
    
    @property
    def is_healthy(self):
            y, p, r = self._cur_euler_ypr
            min_r, max_r = self._healthy_roll_range
            is_healthy = min_r <= r <= max_r
            return is_healthy
    
    @property
    def is_terminated(self):
            y, p, r = self._cur_euler_ypr
            t_min_r, t_max_r = self._terminating_roll_range
            is_not_over = t_min_r <= r <= t_max_r

            is_done = False
            if is_not_over:
                self._unhealth_steps = 0
            else:
                self._unhealth_steps += 1

            if self._unhealth_steps >= self._unhealthy_max_steps:
                is_done = True

            return is_done
    
    def control_cost(self, action):
         control_cost = self._ctrl_cost_weight * np.sum(action)
         return control_cost
    

    def straightness_cost(self, p0: np.ndarray, pt: np.ndarray, direction: np.ndarray, weight: float = 1.0) -> float:
        """
        직진성 비용 계산 함수
        :param p0: 기준점 (원점 좌표) ndarray of shape (2,)
        :param pt: 현재 위치 ndarray of shape (2,)
        :param direction: 목표 방향 (단위벡터) ndarray of shape (2,)
        :param weight: 가중치 (cost 크기 조절)
        :return: 직진성 cost (float)
        """
        # 방향 벡터 정규화
        dir_unit = direction / np.linalg.norm(direction)
        
        # 기준점에서 현재 위치까지의 벡터
        vec = pt - p0
        
        # vec를 기준 직선 방향으로 투영
        proj_length = np.dot(vec, dir_unit)
        proj_vec = proj_length * dir_unit
        
        # 투영 벡터를 빼면 수직 거리 벡터가 됨
        orthogonal_vec = vec - proj_vec
        
        # 거리(norm)를 cost로 사용
        cost = weight * np.linalg.norm(orthogonal_vec)
        
        return cost

            
    def step(self, action):
        com_pos_before = self.get_robot_com().copy()
        com_rpy_before = self.get_robot_rot().copy()
        head_quat_before = self.data.body(self._main_body).xmat.copy()
        head_quat_before = np.reshape(head_quat_before, (3,3)).copy()

        if self._n_step < 1:   
            self._initial_rpy = com_rpy_before.copy()
            self._initial_com = com_pos_before.copy()
            self._initial_head_rpy = Rotation.from_matrix(head_quat_before).as_rotvec(True).copy()

        motion_vector = self._motion_vector.copy()
        direction_action = (action * motion_vector).copy()

        self.do_simulation(direction_action, self.frame_skip)

        com_pos_after = self.get_robot_com().copy()
        com_rpy_after = self.get_robot_rot().copy()
        head_quat_after = self.data.body(self._main_body).xmat.copy()
        head_quat_after = np.reshape(head_quat_after, (3,3)).copy()

        self._n_step += 1

        ## 각종 Transformation matrix 생성
        # Before의 Transformation matrix
        T_1 = np.eye(4)
        T_1[:3, :3] = Rotation.from_rotvec(com_rpy_before,True).as_matrix()
        T_1[:3, 3] = com_pos_before

        # After의 Transformation matrix
        T_2 = np.eye(4)
        T_2[:3, :3] = Rotation.from_rotvec(com_rpy_after,True).as_matrix()
        T_2[:3, 3] = com_pos_after

        # Transformation matrix of CoM between two steps
        d_T = np.linalg.inv(T_1) @ T_2
        d_T_p = d_T[:3, 3]
        d_T_r = d_T[:3, :3]

        # ## Step before와 Step after를 통해서 구하기
        # x_disp = d_T_p[0]
        # y_disp = d_T_p[1]

        ## Origin과 Step after를 통해서 구하기
        # """
        # 학습 초기에는 이 방법을 통해서 속도를 구하는 것으로 변경했음. 학습 초기에는 뱀 로봇이 원하는 방향으로 잘 움직이지 않는데, 너무 타이트한 속도 조건을 요구하는 것으로 생각됨. 이후 어느정도 뱀 로봇이 조향 방향으로 움직이기 시작하면 Step을 통해서 구해진 속도를 사용하는 것으로 변경할 예정임.
        # """

        x_disp, y_disp, z_disp = T_2[:3, 3] - T_1[:3, 3]

        # 회전의 노름 (회전의 크기) 'ZYX' -> 마지막에 Roll축에 왜곡이 생겨서 다른 방법으로 바꿔야함.
        step_euler_ypr = Rotation.from_matrix(d_T_r).as_euler('ZYX',False).copy()
        self._cur_euler_ypr = Rotation.from_rotvec(com_rpy_after,True).as_euler('ZYX',True).copy()

        # 회전의 노름 (회전의 크기) 'ZXY' -> 왜곡 문제 해결을 위해서 XY 순서로 변경
        # step_euler_ypr = Rotation.from_matrix(d_T_r).as_euler('zyx',False).copy() #주의! Yaw Roll Pitch 순서로 저장됨
        # self._cur_euler_ypr = Rotation.from_matrix(d_T0_r).as_euler('zyx',True).copy() #주의! Yaw Roll Pitch 순서로 저장됨

        # norm_r = np.linalg.norm(np.array([self._cur_euler_ypr[1], self._cur_euler_ypr[2]])).copy()
        # norm_r = np.linalg.norm(np.array([self._cur_euler_ypr[0]])).copy() #Roll 방향 일단 무시

        #### Reward 계산을 위한 변수 설정
        tmp_x_vel = x_disp / self.dt
        tmp_y_vel = y_disp / self.dt
        tmp_yaw_vel = step_euler_ypr[0] / self.dt

        if self._use_vels_mov_mean:
            x_vel, y_vel, yaw_vel = self._mov_mean_vels.update(tmp_x_vel, tmp_y_vel, tmp_yaw_vel)

        else:
            x_vel = tmp_x_vel
            y_vel = tmp_y_vel
            yaw_vel = tmp_yaw_vel

        # ## Gait changing...
        self._k += 1
        self._motion_vector = self._gait.getMvec(self._k).copy()
        
        observation = self._get_obs(self._motion_vector)
        reward, reward_info = self._get_rew(x_vel, y_vel, self._joy_input[0], self._joy_input[1], action, self._cur_euler_ypr, yaw_vel, self._joy_input[2], com_pos_after[0:2].copy())
        terminated = self.is_terminated and self._terminate_when_unhealthy
        truncated = self._n_step >= 6000

        if self.render_mode == "human":
            self.render()

        info = {
            "step": self._n_step,
            "action": action.copy(),
            "x_displacement": x_disp,
            "y_displacement": y_disp,
            "distance_from_origin": np.linalg.norm(self.data.qpos[0:2], ord=2),
            "x_velocity": x_vel,
            "y_velocity": y_vel,
            "yaw_velocity": yaw_vel,
            "joint_pos": observation[:14].copy(),
            "joint_vel": observation[-41:-27].copy(),
            "head_quat": observation[-27:-23].copy(),
            "head_ang_vel": observation[-23:-20].copy(),
            "head_lin_acc": observation[-20:-17].copy(),
            "motion_vector": observation[-17:-3].copy(),
            "joy_input": observation[-3:].copy(),
            "com_pos": com_pos_before,
            "com_ypr": self._cur_euler_ypr,
            "step_ypr": step_euler_ypr,
            "init_rpy": self._initial_rpy,
            "init_com": self._initial_com,
            "init_head_rpy":self._initial_head_rpy,
            "gait_params": self._gait_params,
            "friction_coeff": self._friction_information,
            "motionMatrix":self._gait.getMotionMat().copy(),
            **reward_info,
        }

        return observation, reward, terminated, truncated, info

    def _get_rew(self, x_vel, y_vel, joy_x, joy_y, action, cur_ypr, yaw_vel, joy_r, com_pos_after):
        """
        ChatGPT 리팩토링 보상함수
        Norm_r대신 YRP 불러옴
        """
        _v_vel = np.array([x_vel, y_vel])
        _v_joy = np.array([joy_x, joy_y])

        # 벡터 크기
        vel_mag = np.linalg.norm(_v_vel)
        joy_mag = np.linalg.norm(_v_joy)
        yaw_mag = np.abs(yaw_vel)

        # # 정렬 유사도 (선형)
        # if joy_mag > 1e-1 and vel_mag > 1e-1:
        #     direction_similarity = np.dot(_v_vel, _v_joy) / (vel_mag * joy_mag + 5e-2)
        #     direction_similarity = np.clip(direction_similarity, -0.5, 1)
        #     vel_theta = None
        # else:
        #     direction_similarity = 0.0

        # 정렬 유사도 (선형) 방향 세분화 진행
        if joy_mag > 1e-1:
            vel_direction = np.dot(_v_vel, _v_joy) / (vel_mag * joy_mag + 5e-3)
            vel_direction = np.clip(vel_direction, -1, 1)
            vel_theta = np.arccos(vel_direction)

            if self._use_imu_mov_mean:
                vel_theta = self._mov_vel_orient.update(vel_theta)

            direction_similarity = np.cos(vel_theta) - 2 * (vel_theta / np.pi)
            direction_similarity = np.clip(direction_similarity, -1, 1)
        else:
            direction_similarity = 0.0
            vel_theta = 0.0

            if self._use_imu_mov_mean:
                vel_theta = self._mov_vel_orient.update(vel_theta)


        # 선형 움직임 보상
        linear_movement_reward = self._forward_reward_weight * direction_similarity * vel_mag

        # 회전 정렬 보상
        if np.abs(joy_r) > 1e-1 and yaw_mag > 1e-1:
            rotation_alignment = np.sign(joy_r * yaw_vel)
        else:
            rotation_alignment = 0.0

        angular_movement_reward = self._rotation_reward_weight * rotation_alignment * yaw_mag * np.abs(joy_r)

        # 조작 효율성 보상: 적은 조작으로 많은 이동을 유도
        if np.linalg.norm(action) > 1e-3:
            efficiency = direction_similarity * vel_mag / (np.linalg.norm(action) * 1e-2 + 1e-1)
        else:
            efficiency = 0.0

        efficiency_reward = self._efficiency_reward_weight * efficiency

        # 건강 보상
        healthy_reward = self.healthy_reward

        # 보상 총합
        rewards = linear_movement_reward + angular_movement_reward + efficiency_reward + healthy_reward

        # # 비용: 컨트롤, 자세, 회전, 비정상 상태
        # if joy_mag > 1e-1:
        #     ctrl_cost_weight = self._ctrl_cost_weight / joy_mag
        # else:
        #     ctrl_cost_weight = 2 * self._ctrl_cost_weight

        tmp_cur_ypr = cur_ypr
        if self._use_vels_mov_mean:
            # tmp_cur_ypr = self._mov_gait_ypr.update(tmp_cur_ypr[0], tmp_cur_ypr[1], tmp_cur_ypr[2])
            
            # 쿼터니언 윈도우를 사용했을 시
            tmp_rot = Rotation.from_euler('ZYX', tmp_cur_ypr, degrees=True)
            tmp_quat = self._mov_gait_ypr.update(tmp_rot.as_quat(scalar_first=True))
            tmp_cur_ypr = Rotation.from_quat(tmp_quat, scalar_first=True).as_euler('ZYX', degrees=True)

        norm_r = np.linalg.norm(np.array([tmp_cur_ypr[0]])).copy() #Roll Pitch 방향 일단 무시

        ctrl_cost = self._ctrl_cost_weight * np.sum(action) * (1 / 30)
        unhealthy_cost = self.is_terminated * self._unhealthy_cost_weight
        orientation_cost = self._rotation_norm_cost_weight * norm_r * (1 / 20)

        # 방향 정사형 비용 계산
        proj_dist_cost = self._proj_dist_cost_weight * self.straightness_cost(self._initial_com[0:2].copy(), com_pos_after, _v_joy, weight=self._proj_dist_cost_weight)

        yaw_cost_weight = 3 if np.abs(joy_r) < 1e-2 else 0
        yaw_vel_cost = yaw_cost_weight * yaw_mag
 
        costs = ctrl_cost + unhealthy_cost + orientation_cost + yaw_vel_cost + proj_dist_cost
        reward = rewards - costs

        reward_info = {
            "reward_linear_movement": linear_movement_reward,
            "reward_angular_movement": angular_movement_reward,
            "reward_efficiency": efficiency_reward,
            "reward_healthy": healthy_reward,
            "cost_ctrl": -ctrl_cost,
            "cost_unhealthy": -unhealthy_cost,
            "cost_orientation": -orientation_cost,
            "cost_yaw_vel": -yaw_vel_cost,
            "cost_proj_dist": -proj_dist_cost,
            "direction_similarity": direction_similarity,
            "rotation_alignment": rotation_alignment,
            "reward_func_orientation": tmp_cur_ypr,
            "velocity_theta": vel_theta,
        }

        return reward, reward_info



    def _get_obs(self, mVec : np.ndarray):
        """
        Mujoco Sensor Tags
        "head_quat": observation[-10:-6].copy(),
        "head_ang_vel": observation[-6:-3].copy(),
        "head_lin_acc": observation[-3::].copy(),
        """

        tmp = self.data.sensordata.copy()

        if self._use_imu_mov_mean:
            tmp[-10:-6] = self._mov_mean_imu_quat.update((self.data.sensordata[-10].copy(), self.data.sensordata[-9].copy(), self.data.sensordata[-8].copy(), self.data.sensordata[-7].copy()))
            tmp[-6:-3] = self._mov_mean_imu_vel.update(self.data.sensordata[-6].copy(), self.data.sensordata[-5].copy(), self.data.sensordata[-4].copy())
            tmp[-3::] = self._mov_mean_imu_acc.update(self.data.sensordata[-3].copy(), self.data.sensordata[-2].copy(), self.data.sensordata[-1].copy())

        tmp[42:56] = (tmp[42:56]>1).astype(int)
        tmp[56:70] = (tmp[56:70]>1).astype(int)
        return np.concatenate((tmp.flatten(), mVec, self._joy_input), dtype=np.float32)
    
    def reset_model(self):
        # Unhealthy step reset
        self._n_step = 0
        self._k = 0
        self._unhealth_steps = 0
        self._initial_rpy = np.array([0,0,0])
        self._initial_head_rpy = np.array([0,0,0])
        self._initial_com = np.array([-0.4795,0,0.0350])
        self._cur_euler_ypr = np.array([0,0,0])

        # Joy input reset 방향키 처럼  8방위 랜덤
        if self._joy_input_random:
            self._joy_input = np.array([0, 0, 0])

            # 8방향 정의 (정규화된 단위 벡터)
            directions = [
                # np.array([0, 1]),                                # ↑ 30,30,40,40,45
                # np.array([np.sqrt(2)/2, np.sqrt(2)/2]),          # ↗ 30,30,40,40,180
                np.array([1, 0]),                                # → 30,30,40,40,0
                # np.array([np.sqrt(2)/2, -np.sqrt(2)/2]),         # ↘ 30,30,40,40,0
                # np.array([0, -1]),                               # ↓ 30,30,40,40,315
                # np.array([-np.sqrt(2)/2, -np.sqrt(2)/2]),        # ↙ 30,30,40,40,45,-1
                # np.array([-1, 0]),                               # ← 30,30,40,40,180,-1
                # np.array([-np.sqrt(2)/2, np.sqrt(2)/2])          # ↖ 30,30,40,40,315,-1
            ]

            gait_params =[
                # (30, 30, 40, 40, 45),   # ↑
                # (30, 30, 40, 40, 23),  # ↗
                (30, 30, 40, 40, 0),  # →
                # (30, 30, 40, 40, -23),    # ↘
                # (30, 30, 40, 40, -45),  # ↓
                # (30, 30, 40, 40, 23, -1),   # ↙
                # (30, 30, 40, 40, 0, -1),    # ←
                # (30, 30, 40, 40, -23, -1)   # ↖
            ]

            # 랜덤하게 방향 선택
            idx = self.np_random.choice(len(directions))
            direction = directions[idx]

            # z축 회전 없이 출력
            self._joy_input = np.array([direction[0], direction[1], 0])

            self._gait_params = gait_params[idx]

            # Gait reset
            self._gait.reset(params=self._gait_params, frame_skip=self.frame_skip)

        # System reset
        # noise_low = -0.05
        # noise_high = 0.05
        noise_low = 0
        noise_high = 0
        noise_qvel = 0
        xpos_low = 0
        xpos_high = 0

        qpos = self.init_qpos + self.np_random.uniform(
            low=noise_low, high=noise_high, size=self.model.nq
        )

        qvel = (
            self.init_qvel
            + noise_qvel * self.np_random.standard_normal(self.model.nv)
        )
        x_xpos = self.np_random.uniform(low=xpos_low, high=xpos_high)
        y_xpos = self.np_random.uniform(low=xpos_low, high=xpos_high)

        qpos[0] = x_xpos
        qpos[1] = y_xpos

        _temporal_param = max(self._gait_params[2], self._gait_params[3])
        _period = int(( (2 * np.pi) / (_temporal_param / 10) ) * ( 1 / (self.model.opt.timestep * self.frame_skip) ) )  # 좌변 -> 초 단위, 우변 -> 초 단위를 몇 슬롯으로 나눌지
        _period2 = int(( 1 / (self.model.opt.timestep * self.frame_skip) ) * 0.3)

        self._mov_mean_vels.reset(_period)
        self._mov_gait_ypr.reset(_period * 2)
        
        self._mov_mean_imu_vel.reset(_period2)
        self._mov_mean_imu_acc.reset(_period2)
        self._mov_mean_imu_quat.reset(_period2)
        self._mov_vel_orient.reset(_period2)

        if self._use_friction_chg:
            u_slide = round(self.np_random.uniform(low=0.6, high = 0.8),2)
            u_torsion = round(self.np_random.uniform(low=0.013, high = 0.017),3)
            u_roll = round(self.np_random.uniform(low=0.0008, high = 0.0012),4)
            self.model.geom('floor').friction = [u_slide, u_torsion, u_roll]
            self._friction_information = [u_slide, u_torsion, u_roll]

        self.set_state(qpos, qvel)

        _tmp_motion_vector = self._gait.getMvec(0).copy()
        observation = self._get_obs(_tmp_motion_vector)

        return observation
    
    def get_robot_com(self)->np.ndarray:
        accum_x = 0
        accum_y = 0
        accum_z = 0
        len_names = len(self._robot_body_names)

        for name in self._robot_body_names:
            x, y, z = self.data.body(name).xpos
            accum_x = accum_x + x
            accum_y = accum_y + y
            accum_z = accum_z + z

        return np.array([accum_x / len_names, accum_y / len_names, accum_z / len_names])

    def get_robot_rot(self)->np.ndarray: #Chordal L2 method
        com_roll = 0
        com_pitch = 0
        com_yaw = 0

        robot_quats = np.empty((0,4))
        for name in self._robot_body_names:
            robot_quats = np.vstack((robot_quats, self.data.body(name).xquat.copy()))

        robot_quats = robot_quats[:, [1, 2, 3, 0]]
        robot_rot = Rotation(robot_quats)

        com_roll, com_pitch, com_yaw = robot_rot.mean().as_rotvec(True)

        return np.array([com_roll, com_pitch, com_yaw])

    def do_simulation(self, ctrl, n_frames):
        return super().do_simulation(ctrl, n_frames)
