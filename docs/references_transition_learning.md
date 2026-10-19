# 전문가 정책 통합·보행 전환 학습 참고문헌 (Horcrux v2)

## 개요

Horcrux v2는 MuJoCo에서 시뮬레이션되는 14-DOF 뱀 로봇으로, "보행 분해(Gait Decomposition, GD)" 제어 패러다임을
사용한다. serpenoid 보행 생성기가 매 스텝 위상에 따라 바뀌는 관절별 부호 패턴(motion vector, ±1)을 만들고,
PPO(Stable-Baselines3 + VecNormalize) 정책은 비음수 진폭 [0, 2.7]만 출력하여 부호 패턴에 곱한다. 즉 보행이
"어느 방향으로"를, 정책이 "얼마나 세게"를 결정한다. 현재 8개 평면 방향(전/후/좌/우/대각 4, 각기 다른 위상
오프셋 δ, 후진은 시간 역전 보행)과 CW/CCW 제자리 회전을 담당하는 10개 전문가 정책이 있으며, 경로 추종은
전문가 간 전환으로 수행된다. 전환 실패 문제는 "위상 정렬"(현재 motion vector와 가장 유사한 부호 패턴을 갖는
사이클 위상에서 새 보행을 시작)과 짧은 행동 크로스페이드로 해결했다.

다음 단계는 (1) **증류**: 10개 전문가를 행동 복제(BC)로 하나의 명령 조건부 정책에 증류(필요 시 DAgger 보정,
Monte-Carlo 수익에 대한 critic 사전 회귀, 보수적 탐색 표준편차)하여 PPO 체크포인트로 로드 가능하게 만들고,
(2) **전환 RL 미세조정**: 에피소드 도중 무작위 명령 전환(10개 명령 중 무작위 순서쌍, 무작위 전환 시점,
무작위 초기 보행 위상)이 일어나는 환경에서 위상 정렬 전환을 적용한 채 PPO로 미세조정하여 정책 스스로
안정적이고 매끄러운 보행 전환을 학습하게 하며, (3) **지속 학습**: 이후 새 작업을 망각 없이 추가하는 것이다.

아래 절은 이 파이프라인에 대응된다. 1절(PPO 기초)은 전 단계의 공통 기반, 2·3절은 (1) 증류, 4·5절은 (1)→(2)
경계(BC 정책의 PPO 워밍업과 다중 명령 최적화), 6절은 (3) 지속 학습, 7·8절은 (2) 보행 전환 환경 설계와 위상
처리를 뒷받침한다. 모든 항목은 2026-09-09에 웹(arXiv 초록 페이지, 출판사 페이지, Crossref, 학회 프로시딩)으로
서지 정보를 검증했다. `[추가]` 표시는 후보 목록 외에 추가한 항목이다.

---

## 1. PPO / on-policy 기초

- **Proximal Policy Optimization Algorithms** — John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov (arXiv preprint, 2017). arXiv:1707.06347
  - 관련성: 전문가 학습과 (2) 전환 미세조정 모두의 기반 알고리즘(clipped surrogate, 상태 독립 log_std). 증류된 정책을 PPO 체크포인트로 로드할 때 어떤 파라미터(actor, critic, log_std)가 목적함수에 어떻게 들어가는지의 근거.

- **High-Dimensional Continuous Control Using Generalized Advantage Estimation** — John Schulman, Philipp Moritz, Sergey Levine, Michael Jordan, Pieter Abbeel (ICLR 2016). arXiv:1506.02438
  - 관련성: GAE(γ, λ)와 "경험 수익에 대한 가치함수 회귀"를 정식화. (1)의 critic 사전 회귀(MC 수익 회귀)가 PPO의 advantage 추정과 정합하는 이유를 설명한다.

- **What Matters In On-Policy Reinforcement Learning? A Large-Scale Empirical Study** — Marcin Andrychowicz, Anton Raichuk, Piotr Stańczyk, Manu Orsini, Sertan Girgin, Raphael Marinier, Léonard Hussenot, Matthieu Geist, Olivier Pietquin, Marcin Michalski, Sylvain Gelly, Olivier Bachem (ICLR 2021; 학회판 제목 "What Matters for On-Policy Deep Actor-Critic Methods? A Large-Scale Study"). arXiv:2006.05990
  - 관련성: 25만 에이전트 실험으로 초기 정책 표준편차, 마지막 층 초기화 스케일, 관측·가치·advantage 정규화의 영향을 정량화. (1)의 "보수적 탐색 std" 설정값과 VecNormalize 유지 결정의 직접 근거.

- **Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO** — Logan Engstrom, Andrew Ilyas, Shibani Santurkar, Dimitris Tsipras, Firdaus Janoos, Larry Rudolph, Aleksander Madry (ICLR 2020). arXiv:2005.12729
  - 관련성: 가치 클리핑, 보상 스케일링, 직교 초기화, 관측 정규화 같은 "코드 수준 최적화"가 성능을 좌우함을 보임. BC 정책을 PPO로 넘길 때 정규화 통계(VecNormalize)와 critic 상태를 함께 이관해야 하는 이유.

- **Deep Reinforcement Learning that Matters** — Peter Henderson, Riashat Islam, Philip Bachman, Joelle Pineau, Doina Precup, David Meger (AAAI 2018). arXiv:1709.06560
  - 관련성: 시드 간 분산과 보고 방식의 문제를 지적. (2)의 전환 성공률 평가(명령 쌍 × 전환 시점 × 시드)를 다중 시드·신뢰구간으로 보고해야 함을 뒷받침.

---

## 2. 행동 복제(BC) / DAgger / 복합 오차

- **ALVINN: An Autonomous Land Vehicle in a Neural Network** — Dean A. Pomerleau (Advances in Neural Information Processing Systems 1, NIPS 1988 학회, 1989 출판, pp. 305–313). https://proceedings.neurips.cc/paper/1988/hash/812b4ba287f5ee0bc9d43bbf5bbe87fb-Abstract.html
  - 관련성: 시연을 지도학습으로 모사하는 BC의 원형. (1)에서 "전문가 정책 출력을 지도학습 목표로 삼는다"는 접근의 출발점으로 인용.

- **Efficient Reductions for Imitation Learning** — Stephane Ross, Drew Bagnell (AISTATS 2010, PMLR 9:661–668). https://proceedings.mlr.press/v9/ross10a.html
  - 관련성: 순수 BC의 오차가 시간 지평에 대해 2차(T²)로 누적됨을 증명하고 forward training·SMILe을 제안. (1)에서 BC만으로는 전환 직후의 분포 이동을 감당하기 어렵다는 논거.

- **A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning** — Stephane Ross, Geoffrey J. Gordon, J. Andrew Bagnell (AISTATS 2011). arXiv:1011.0686
  - 관련성: DAgger. 학생 정책이 방문한 상태에 전문가 라벨을 붙여 데이터셋을 누적. 본 프로젝트는 10개 전문가를 언제든 질의할 수 있으므로 (1)의 DAgger 보정을 저비용으로 구현할 수 있다.

- [추가] **End-to-end Driving via Conditional Imitation Learning** — Felipe Codevilla, Matthias Müller, Antonio López, Vladlen Koltun, Alexey Dosovitskiy (ICRA 2018). arXiv:1710.02410
  - 관련성: 고수준 명령(좌/우/직진)을 입력으로 받는 "명령 조건부 BC"를 정식화하고, 명령을 단순 결합하는 방식과 명령별 분기(branch) 헤드를 비교. (1)의 10개 명령 조건부 단일 정책 아키텍처(one-hot 입력 vs 분기 헤드) 선택 근거.

---

## 3. 정책 증류 / 다중 전문가 통합

- **Distilling the Knowledge in a Neural Network** — Geoffrey Hinton, Oriol Vinyals, Jeff Dean (NIPS 2014 Deep Learning Workshop; arXiv 2015). arXiv:1503.02531
  - 관련성: 지식 증류의 원전(soft target, temperature). (1)에서 전문가 가우시안 정책의 평균만 회귀할지, 분포(평균+표준편차)를 KL로 맞출지 결정할 때의 개념적 기반.

- **Policy Distillation** — Andrei A. Rusu, Sergio Gomez Colmenarejo, Caglar Gulcehre, Guillaume Desjardins, James Kirkpatrick, Razvan Pascanu, Volodymyr Mnih, Koray Kavukcuoglu, Raia Hadsell (ICLR 2016). arXiv:1511.06295
  - 관련성: 여러 DQN 교사를 단일 학생 네트워크로 증류(다중 작업 증류)하며 손실 함수(MSE/NLL/KL) 비교. (1)의 "10개 전문가 → 1개 정책" 증류의 표준 참조.

- **Actor-Mimic: Deep Multitask and Transfer Reinforcement Learning** — Emilio Parisotto, Jimmy Lei Ba, Ruslan Salakhutdinov (ICLR 2016). arXiv:1511.06342
  - 관련성: 정책 회귀 + 특징 회귀 목적으로 다중 전문가를 하나의 네트워크에 모사하고, 이를 새 작업 전이의 초기화로 사용. (1)→(3)으로 이어지는 "증류된 정책을 전이 초기화로 쓰는" 구도와 동일.

- **Distral: Robust Multitask Reinforcement Learning** — Yee Whye Teh, Victor Bapst, Wojciech Marian Czarnecki, John Quan, James Kirkpatrick, Raia Hadsell, Nicolas Heess, Razvan Pascanu (NeurIPS 2017). arXiv:1707.04175
  - 관련성: 작업별 정책을 공유 "증류 정책"에 KL로 묶으면서 동시 학습. (2)에서 단일 정책을 미세조정할 때 전문가 행동으로부터의 KL 정규화를 추가하는 대안 설계의 근거.

- **Neural probabilistic motor primitives for humanoid control** — Josh Merel, Leonard Hasenclever, Alexandre Galashov, Arun Ahuja, Vu Pham, Greg Wayne, Yee Whye Teh, Nicolas Heess (ICLR 2019). arXiv:1811.11711
  - 관련성: 수천 개의 운동 클립 전문가를 잠재 변수 조건부 단일 정책으로 지도 증류하고, 잠재 공간에서 기술 간 매끄러운 전환을 얻음. (1)의 통합 정책 구조와 (2)의 "전환도 정책이 표현"한다는 목표의 선례.

- **Kickstarting Deep Reinforcement Learning** — Simon Schmitt, Jonathan J. Hudson, Augustin Zidek, Simon Osindero, Carl Doersch, Wojciech M. Czarnecki, Joel Z. Leibo, Heinrich Kuttler, Andrew Zisserman, Karen Simonyan, S. M. Ali Eslami (arXiv preprint, 2018). arXiv:1803.03835
  - 관련성: RL 손실에 교사 정책과의 KL 보조 손실을 가중치 감쇠(annealing)로 더해 학생이 교사를 빠르게 넘어서게 함. (2)의 PPO 미세조정 중 전문가 행동을 잃지 않도록 하는 보조 손실 설계에 직접 적용 가능.

- **Progress & Compress: A scalable framework for continual learning** — Jonathan Schwarz, Jelena Luketina, Wojciech M. Czarnecki, Agnieszka Grabska-Barwinska, Yee Whye Teh, Razvan Pascanu, Raia Hadsell (ICML 2018). arXiv:1805.06370
  - 관련성: 새 작업은 활성 열(RL)로 배우고, 지식 베이스에는 증류 + online EWC로 압축. (3)에서 새 명령을 추가할 때 "학습 → 증류 → 보호" 주기를 반복하는 운영 절차의 모델.

- [추가] **Distilling Policy Distillation** — Wojciech Marian Czarnecki, Razvan Pascanu, Simon Osindero, Siddhant M. Jayakumar, Grzegorz Swirszcz, Max Jaderberg (AISTATS 2019). arXiv:1902.02186
  - 관련성: 증류 데이터를 교사 궤적에서 모을지 학생 궤적에서 모을지, 엔트로피 정규화 여부 등 정책 증류 변형들의 수렴 특성을 분석. (1)에서 BC(교사 상태) → DAgger(학생 상태) 전환 시점과 혼합 비율을 정하는 이론적 근거.

---

## 4. BC·시연으로부터 RL 워밍업/미세조정 (critic 초기화 문제 포함)

- **Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations** — Aravind Rajeswaran, Vikash Kumar, Abhishek Gupta, Giulia Vezzani, John Schulman, Emanuel Todorov, Sergey Levine (RSS 2018). arXiv:1709.10087
  - 관련성: DAPG. BC로 정책을 초기화한 뒤 정책 경사에 시연 항을 가중 감쇠로 더해 미세조정. "BC 초기화 + on-policy 정책 경사" 조합의 대표 사례로, (1)→(2) 이관 절차의 기본 템플릿.

- **Overcoming Exploration in Reinforcement Learning with Demonstrations** — Ashvin Nair, Bob McGrew, Marcin Andrychowicz, Wojciech Zaremba, Pieter Abbeel (ICRA 2018). arXiv:1709.10089
  - 관련성: BC 보조 손실에 Q-filter(정책이 시연보다 나을 때 BC 손실 무시)를 두고, 시연 상태에서 에피소드를 시작하는 리셋 기법을 제안. (2)의 무작위 초기 보행 위상 리셋과 "전문가보다 나아지면 모사 손실을 끊는" 규칙의 근거.

- **Jump-Start Reinforcement Learning** — Ikechukwu Uchendu, Ted Xiao, Yao Lu, Banghua Zhu, Mengyuan Yan, Joséphine Simon, Matthew Bennice, Chuyuan Fu, Cong Ma, Jiantao Jiao, Sergey Levine, Karol Hausman (ICML 2023, PMLR 202:34556–34583). arXiv:2204.02372
  - 관련성: 안내 정책(기존 정책)이 초반 h 스텝을 담당하고 탐색 정책이 이어받되 h를 점차 줄이는 커리큘럼. (2)에서 전환 직후 구간만 새 정책이 담당하도록 시작하여 점진적으로 범위를 넓히는 커리큘럼 설계에 적용 가능.

- **Efficient Online Reinforcement Learning with Offline Data** — Philip J. Ball, Laura Smith, Ilya Kostrikov, Sergey Levine (ICML 2023). arXiv:2302.02948
  - 관련성: RLPD. 오프라인 데이터를 대칭 샘플링하고 critic에 LayerNorm을 두어 사전 학습 없이도 안정적으로 온라인 학습. PPO 미세조정이 비효율적일 경우 전문가 궤적을 오프라인 데이터로 쓰는 off-policy 대안 경로.

- **Cal-QL: Calibrated Offline RL Pre-Training for Efficient Online Fine-Tuning** — Mitsuhiko Nakamoto, Yuexiang Zhai, Anikait Singh, Max Sobol Mark, Yi Ma, Chelsea Finn, Aviral Kumar, Sergey Levine (NeurIPS 2023). arXiv:2303.05479
  - 관련성: 사전 학습된 가치함수가 실제 수익 스케일과 어긋나면 온라인 미세조정 초기에 성능이 급락("unlearning")함을 보이고 가치 보정을 제안. (1)의 critic을 MC 수익에 사전 회귀시켜 PPO 초기 advantage가 왜곡되지 않게 하는 조치의 핵심 근거.

- [추가] **Fine-tuning Reinforcement Learning Models is Secretly a Forgetting Mitigation Problem** — Maciej Wołczyk, Bartłomiej Cupiał, Mateusz Ostaszewski, Michał Bortkiewicz, Michał Zając, Razvan Pascanu, Łukasz Kuciński, Piotr Miłoś (ICML 2024, spotlight). arXiv:2402.02868
  - 관련성: 사전 학습 RL 모델을 미세조정하면 초반에 방문하지 않는 상태의 능력이 먼저 망각되며, 지속 학습 기법(EWC, BC 정규화 등)이 이를 완화함을 보임. (2)에서 전환 구간만 학습하다가 정상 보행 능력을 잃는 위험과 그 대책을 정확히 지적.

---

## 5. 다중 작업 RL 최적화

- **Gradient Surgery for Multi-Task Learning** — Tianhe Yu, Saurabh Kumar, Abhishek Gupta, Sergey Levine, Karol Hausman, Chelsea Finn (NeurIPS 2020). arXiv:2001.06782
  - 관련성: PCGrad. 작업 간 상충하는 경사를 사영하여 간섭을 줄임. (1)의 10개 명령 동시 BC나 (2)의 다중 명령 PPO 배치에서 방향별 경사가 상충할 때(예: 전진 vs 회전) 적용 가능한 최적화 기법.

- **Multi-task Deep Reinforcement Learning with PopArt** — Matteo Hessel, Hubert Soyer, Lasse Espeholt, Wojciech Czarnecki, Simon Schmitt, Hado van Hasselt (AAAI 2019, Proc. AAAI 33:3796–3803). arXiv:1809.04474
  - 관련성: 작업별로 가치 목표를 적응 정규화해 보상 스케일이 다른 작업이 학습을 지배하지 못하게 함. VecNormalize는 수익을 전역으로만 정규화하므로, (2)에서 명령별(전진/회전) 수익 스케일 차이를 다룰 때 명령별 가치 정규화의 근거.

---

## 6. 지속 강화학습

- **Overcoming catastrophic forgetting in neural networks** — James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A. Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, Demis Hassabis, Claudia Clopath, Dharshan Kumaran, Raia Hadsell (PNAS 114(13):3521–3526, 2017). DOI 10.1073/pnas.1611835114, arXiv:1612.00796
  - 관련성: EWC. Fisher 정보로 중요 가중치를 보호하는 2차 페널티. (3)에서 새 명령을 추가할 때, 그리고 (2)의 미세조정 중 기존 보행 능력 보호에 가장 먼저 시도할 정규화 기법.

- **Progressive Neural Networks** — Andrei A. Rusu, Neil C. Rabinowitz, Guillaume Desjardins, Hubert Soyer, James Kirkpatrick, Koray Kavukcuoglu, Razvan Pascanu, Raia Hadsell (arXiv preprint, 2016). arXiv:1606.04671
  - 관련성: 이전 열을 동결하고 측면 연결로 새 열을 추가해 망각을 원천 차단(파라미터 증가가 비용). (3)에서 정규화 기반 방법과 비교할 구조 확장형 대안.

- **Towards Continual Reinforcement Learning: A Review and Perspectives** — Khimya Khetarpal, Matthew Riemer, Irina Rish, Doina Precup (Journal of Artificial Intelligence Research 75:1401–1476, 2022). arXiv:2012.13490, https://jair.org/index.php/jair/article/view/13673
  - 관련성: 지속 RL의 문제 정식화와 방법 분류(비정상성의 범위·원인). (3)의 문제 설정을 문헌 용어로 위치시키고 평가 지표(망각, 전이)를 정하는 데 참조.

- **Continual World: A Robotic Benchmark For Continual Reinforcement Learning** — Maciej Wołczyk, Michał Zając, Razvan Pascanu, Łukasz Kuciński, Piotr Miłoś (NeurIPS 2021). arXiv:2105.10919
  - 관련성: 로봇 조작 작업 시퀀스에서 EWC, PackNet, 리플레이 등 지속 학습 기법의 망각·전이 트레이드오프를 체계 비교. (3)에서 기법을 고르고 실험 프로토콜(작업 순서, 지표)을 설계할 때의 벤치마크 참조.

---

## 7. 보행 조건부·다중 보행 다리 로봇 RL 및 보행 전환

- **Multi-expert learning of adaptive legged locomotion** — Chuanyu Yang, Kai Yuan, Qiuguo Zhu, Wanming Yu, Zhibin Li (Science Robotics 5(49):eabb2174, 2020). DOI 10.1126/scirobotics.abb2174
  - 관련성: MELA. 사전 학습된 전문가 DNN들을 게이팅 네트워크로 합성해 전문가 간 "전환 기술"까지 획득. 본 프로젝트의 10개 전문가 통합과 가장 직접적으로 대응하며, 증류 대신 게이팅 합성을 쓰는 대안과 비교 기준.

- **Walk These Ways: Tuning Robot Control for Generalization with Multiplicity of Behavior** — Gabriel B. Margolis, Pulkit Agrawal (CoRL 2022, oral). arXiv:2212.03238
  - 관련성: 보행 파라미터(위상 오프셋, 주파수, 높이 등)를 명령으로 받는 단일 정책을 학습 중 파라미터를 무작위로 바꿔가며 훈련. (1)의 명령 조건부 정책과 (2)의 에피소드 내 무작위 명령 변경 커리큘럼의 직접 선례.

- **Learning quadrupedal locomotion over challenging terrain** — Joonho Lee, Jemin Hwangbo, Lorenz Wellhausen, Vladlen Koltun, Marco Hutter (Science Robotics 5(47):eabc5986, 2020). DOI 10.1126/scirobotics.abc5986, arXiv:2010.11251
  - 관련성: 특권 정보 교사를 학생 정책에 모사시키되 학생 자신의 궤적으로 데이터를 모으는(DAgger식) 교사-학생 훈련과 지형 커리큘럼. (1)의 DAgger 보정을 보행 정책에 적용한 검증된 절차.

- **Learning agile and dynamic motor skills for legged robots** — Jemin Hwangbo, Joonho Lee, Alexey Dosovitskiy, Dario Bellicoso, Vassilios Tsounis, Vladlen Koltun, Marco Hutter (Science Robotics 4(26):eaau5872, 2019). DOI 10.1126/scirobotics.aau5872, arXiv:1901.08652
  - 관련성: PPO 기반 다리 로봇 정책의 실기 전이와 넘어짐 복구 같은 이질적 기술 학습. 관측 설계·보상 설계·PPO 설정의 참조점이며 (2)의 안정성 보상 설계에 참고.

- **Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning** — Nikita Rudin, David Hoeller, Philipp Reist, Marco Hutter (CoRL 2021). arXiv:2109.11978
  - 관련성: 대규모 병렬 PPO와 게임식 지형 커리큘럼. 에피소드 도중 속도 명령을 주기적으로 재샘플링하는 학습 환경 관행의 대표 사례로, (2)의 에피소드 내 무작위 명령 전환 설계를 정당화.

- **RMA: Rapid Motor Adaptation for Legged Robots** — Ashish Kumar, Zipeng Fu, Deepak Pathak, Jitendra Malik (RSS 2021). arXiv:2107.04034
  - 관련성: 1단계 RL 기저 정책 + 2단계 적응 모듈을 배포 정책 자신의 궤적에 대한 지도 회귀로 학습. "정책 자신의 상태 분포에서 지도 학습"이라는 (1)의 DAgger 보정 원리를 보행 정책에서 실증.

- **Sim-to-Real Transfer of Robotic Control with Dynamics Randomization** — Xue Bin Peng, Marcin Andrychowicz, Wojciech Zaremba, Pieter Abbeel (ICRA 2018). arXiv:1710.06537
  - 관련성: 동역학 무작위화로 강건한 정책 획득. (2)의 전환 학습 환경에서 마찰·질량 등 동역학을 무작위화하여 전환의 강건성을 높이고 실기 이관을 준비하는 근거.

- [추가] **Sim-to-Real Learning of All Common Bipedal Gaits via Periodic Reward Composition** — Jonah Siekmann, Yesh Godse, Alan Fern, Jonathan Hurst (ICRA 2021). arXiv:2011.01387
  - 관련성: 주기적 보상 합성과 보행 파라미터(위상 비율·오프셋) 입력으로 단일 정책이 모든 일반 2족 보행을 학습하고, 명령 변경만으로 보행 간 전환을 수행. (2)의 "단일 명령 조건부 정책이 전환까지 학습한다"는 목표의 가장 가까운 실증.

- [추가] **Learning Free Gait Transition for Quadruped Robots via Phase-Guided Controller** — Yecheng Shao, Yongbin Jin, Xianwei Liu, Weiyan He, Hongtao Wang, Wei Yang (IEEE Robotics and Automation Letters, 2022). DOI 10.1109/LRA.2021.3136645, arXiv:2201.00206
  - 관련성: 위상 신호로 안내되는 정책이 위상 관계 변경만으로 보행 간 자유 전환을 학습. 본 프로젝트의 "위상 정렬 전환"을 정책 학습 문제로 옮기는 (2)의 설계와 직접 비교 가능.

- [추가] **CPG-RL: Learning Central Pattern Generators for Quadruped Locomotion** — Guillaume Bellegarda, Auke Ijspeert (IEEE Robotics and Automation Letters 7(4):12547–12554, 2022). DOI 10.1109/LRA.2022.3218167, arXiv:2211.00458
  - 관련성: CPG가 리듬을, RL 정책이 진폭·주파수 설정값을 담당하는 분업 구조로 전방향 보행을 학습. GD 패러다임(보행기가 부호, 정책이 진폭)을 CPG-RL 계열로 위치시키는 근거이며 위상 처리 방식 참조.

---

## 8. 뱀 로봇, serpenoid 보행, CPG 위상 처리

- **Biologically Inspired Robots: Snake-Like Locomotors and Manipulators** — Shigeo Hirose (역: Peter Cave, Charles Goulden) (Oxford University Press, 1993). ISBN 978-0-19-856261-0
  - 관련성: serpenoid 곡선과 능동 코드 기구(ACM)의 원전. 본 프로젝트 보행 생성기의 수학적 기초 인용처.

- **Parameterized and Scripted Gaits for Modular Snake Robots** — Matthew Tesch, Kevin Lipkin, Isaac Brown, Ross Hatton, Aaron Peck, Justine Rembisz, Howie Choset (Advanced Robotics 23(9):1131–1158, 2009). DOI 10.1163/156855309X452566
  - 관련성: 오프셋·진폭·주파수·위상으로 이루어진 공통 매개변수식으로 다양한 보행(사이드와인딩, 롤링 등)을 기술. 8방향 전문가가 공유하는 보행 매개변수화와 위상 오프셋 δ의 정의 근거.

- **A review on modelling, implementation, and control of snake robots** — P. Liljebäck, K. Y. Pettersen, Ø. Stavdahl, J. T. Gravdahl (Robotics and Autonomous Systems 60(1):29–40, 2012). DOI 10.1016/j.robot.2011.08.010
  - 관련성: 뱀 로봇 모델링·제어의 종합 리뷰. 경로 추종 제어 문헌 맥락에서 본 프로젝트의 학습 기반 접근을 위치시킬 때 인용.

- **Central pattern generators for locomotion control in animals and robots: A review** — Auke Jan Ijspeert (Neural Networks 21(4):642–653, 2008). DOI 10.1016/j.neunet.2008.03.014
  - 관련성: CPG의 위상 결합, 구동 신호에 의한 보행 전환, 감각 피드백 통합을 정리. 보행 생성기의 위상 상태를 정책 관측에 포함하고 전환 시 위상을 다루는 (2)의 설계 언어.

- **Locomotion Control of a Biped Robot Using Nonlinear Oscillators** — S. Aoi, K. Tsuchiya (Autonomous Robots 19:219–232, 2005). DOI 10.1007/s10514-005-4051-1
  - 관련성: 접지 이벤트에서 진동자 위상을 재설정(phase resetting)하여 보행을 안정화. 본 프로젝트의 "전환 시 위상 정렬"은 이 위상 재설정 개념의 뱀 로봇판으로 해석할 수 있다.

- [추가] **From Swimming to Walking with a Salamander Robot Driven by a Spinal Cord Model** — Auke Jan Ijspeert, Alessandro Crespi, Dimitri Ryczko, Jean-Marie Cabelguen (Science 315:1416–1420, 2007). DOI 10.1126/science.1138353
  - 관련성: 단일 구동 신호의 변화만으로 CPG가 수영↔보행 전환을 매끄럽게 수행. 명령 변화 → 보행 전환을 하나의 생성 구조 안에서 다루는 (2)의 생물학·로봇학적 근거.

- [추가] **Energy-efficient and damage-recovery slithering gait design for a snake-like robot based on reinforcement learning and inverse reinforcement learning** — Z. Bing, C. Lemke, L. Cheng, K. Huang, A. Knoll (Neural Networks 129:323–333, 2020). DOI 10.1016/j.neunet.2020.05.029
  - 관련성: 뱀 로봇에 PPO로 속도 범위 전반의 슬리더링 보행을 학습하고, RL 전문가 궤적으로 IRL 제어기를 학습. 뱀 로봇 PPO 학습과 "전문가 궤적 재활용"의 선행 사례.

- [추가] **Distributed Learning of Decentralized Control Policies for Articulated Mobile Robots** — Guillaume Sartoretti, William Paivine, Yunfei Shi, Yue Wu, Howie Choset (IEEE Transactions on Robotics, 2019). DOI 10.1109/TRO.2019.2922493, arXiv:1901.08537
  - 관련성: 모듈형 뱀 로봇에서 매개변수 보행 위에 RL 정책을 얹어 모듈 간 공유 정책을 분산 학습. "보행 구조 + 학습 정책" 조합을 뱀 로봇에 적용한 직접 선행 연구.

- [추가] **Optimizing snake robot locomotion with decomposed gait pattern representation** — Bongsub Song, Insung Ju, Dongwon Yun (Integrated Computer-Aided Engineering 32(2):196–225, 2025). DOI 10.1177/10692509251316676
  - 관련성: 본 프로젝트의 GD 패러다임 원전. motion matrix(부호 패턴)로 보행 특성을 보존하면서 매개변수를 조정하는 보행 분해와 GPG 최적화를 제안. 정책이 진폭만 출력하는 설계와 위상 정렬(motion vector 유사도)의 근거.

---

## 9. 전환 위상 선택의 수학적 근거 (극한 주기 궤도, 점근 위상, 시작 집합)

2026-09-11 추가. 상태 인식 시작 위상 규칙("목표 gait의 주기 궤도에서 가장 가까운 점")의 이론적 배경이다.
부호 정렬은 이 규칙의 0차 근사이며, δ+180° 가족 간 전환에서는 부호 일치 상한(14 중 5~6)이 구조적으로 존재한다.
정리 덱은 `docs/Horcrux_phase_selection_math_2026-09.pptx`, 평가 스크립트는 `training/eval_phase_rules.py`.

- [추가] **The Geometry of Biological Time** — Arthur T. Winfree (Springer, 1980; 2판 Interdisciplinary Applied Mathematics 12, 2001). ISBN 0-387-98992-7, DOI 10.1007/978-1-4757-3484-3 (2판)
  - 관련성: 극한 주기 궤도 밖의 점에 위상을 부여하는 점근 위상(asymptotic phase)과 위상 재설정의 원전. "궤도에서 가장 가까운 점 = 점근 위상의 국소 근사"라는 해석의 근거.

- [추가] **Isochrons and phaseless sets** — John Guckenheimer (Journal of Mathematical Biology 1:259–273, 1975). DOI 10.1007/BF01273747
  - 관련성: 안정 극한 주기 궤도의 등위상선(isochron)이 존재하고 흡인 영역을 엽층화함을 증명. 전환 시 상태 점프와 시작 위상 선택을 등위상선 위의 선택으로 해석하는 근거.

- [추가] **Hybrid Zero Dynamics of Planar Biped Walkers** — E. R. Westervelt, J. W. Grizzle, D. E. Koditschek (IEEE Transactions on Automatic Control 48(1):42–56, 2003). DOI 10.1109/TAC.2002.806653
  - 관련성: 보행을 지수 안정한 주기 궤도로 다루는 대표 문헌. 전문가 정책+gait의 폐루프를 안정 주기 궤도로 보고 전환을 궤도 사이의 점프로 모델링하는 관점의 인용처.

- [추가] **Motion Graphs** — Lucas Kovar, Michael Gleicher, Frédéric Pighin (ACM Transactions on Graphics 21(3):473–482, 2002; SIGGRAPH 2002). DOI 10.1145/566570.566605
  - 관련성: 동작 클립 사이의 전환 지점을 자세·속도 거리(가중 노름)가 작은 프레임 쌍으로 고른다. "궤도 최근접점" 규칙의 직접적 유사 사례이며 가중 거리 설계의 참고.

- [추가] **Skill Discovery in Continuous Reinforcement Learning Domains using Skill Chaining** — George Konidaris, Andrew G. Barto (Advances in Neural Information Processing Systems 22, 2009)
  - 관련성: 스킬의 시작 집합(initiation set)을 성공/실패 데이터로 분류기 학습. "인계 시작 학습 = 시작 집합 확장, 위상 규칙 = 시작 집합 내부 점 선택"이라는 정리와 분류기 기반 위상 선택의 근거.

- [추가] **Geometric Control of Mechanical Systems: Modeling, Analysis, and Design for Simple Mechanical Control Systems** — Francesco Bullo, Andrew D. Lewis (Springer, Texts in Applied Mathematics 49, 2005). ISBN 978-0-387-22195-3, DOI 10.1007/978-1-4899-7276-7
  - 관련성: 질량 행렬(관성 텐서)을 배위 공간의 리만 계량으로 쓰는 표준 정식화. 속도 불일치의 운동 에너지 ½Δθ̇ᵀM(θ)Δθ̇ 를 "전환 에너지"로 쓰는 가중치 선택의 근거.

---

## 본 프로젝트 파이프라인과의 대응표

| 파이프라인 구성 요소 | 핵심 참고문헌 (약칭) |
|---|---|
| BC 증류 (10 전문가 → 1 정책) | Rusu 2016 (Policy Distillation); Parisotto 2016 (Actor-Mimic); Merel 2019 (NPMP); Czarnecki 2019 |
| DAgger 보정 | Ross 2011 (DAgger); Ross & Bagnell 2010; Lee 2020 (Sci. Robotics); Kumar 2021 (RMA) |
| critic 사전 회귀 (MC 수익) | Schulman 2016 (GAE); Nakamoto 2023 (Cal-QL); Andrychowicz 2021; Engstrom 2020 |
| 보수적 log_std 초기화 | Andrychowicz 2021; Rajeswaran 2018 (DAPG); Schulman 2017 (PPO); Wołczyk 2024 |
| 명령 조건부 단일 정책 | Codevilla 2018 (CIL); Margolis 2022 (Walk These Ways); Siekmann 2021; Hessel 2019 (PopArt) |
| 위상 정렬 전환 | Aoi & Tsuchiya 2005; Ijspeert 2008; Shao 2022; Ijspeert 2007; Song 2025 (GD) |
| 상태 인식 시작 위상 (궤도 최근접점, 9절) | Winfree 1980; Guckenheimer 1975; Westervelt 2003 (HZD); Kovar 2002 (Motion Graphs); Konidaris & Barto 2009; Bullo & Lewis 2005; Aoi & Tsuchiya 2005 |
| 무작위 전환 커리큘럼 (에피소드 내 명령 전환) | Rudin 2022; Siekmann 2021; Margolis 2022; Uchendu 2023 (JSRL) |
| PPO 미세조정 중 전문가 행동 유지 | Schmitt 2018 (Kickstarting); Nair 2018; Teh 2017 (Distral); Wołczyk 2024 |
| 지속 학습 확장 (새 작업 추가) | Kirkpatrick 2017 (EWC); Schwarz 2018 (Progress & Compress); Rusu 2016 (Progressive NN); Wołczyk 2021 (Continual World); Khetarpal 2022 |

---

**검증 메모 (2026-09-09):** 위 48개 항목(후보 38 + 추가 10)의 제목·저자·게재처·연도·arXiv ID/DOI는 모두
웹 검색과 arXiv 초록 페이지, 출판사 페이지(Science, PNAS, Springer, Elsevier, SAGE), Crossref API, 학회
프로시딩(NeurIPS, PMLR, AAAI, JAIR) 조회로 확인했다. 검증 실패로 제외한 항목은 없다. 참고 사항: (a) Schulman 2017
PPO, Schmitt 2018 Kickstarting, Rusu 2016 Progressive NN은 arXiv 프리프린트로만 공개되어 학회 정보가 없다.
(b) Andrychowicz et al.의 ICLR 2021 학회판 제목은 arXiv판과 다르다(본문에 병기). (c) Sartoretti 2019는 DOI까지
확인했으나 권·호·쪽수는 조회하지 않았다. (d) Song et al.의 초기 arXiv판(arXiv:2112.02057, "Snake Robot Gait
Decomposition and Gait Parameter Optimization")은 저자가 철회(withdrawn) 상태이므로 저널판만 인용한다.
(e) Laskey et al. 2017 "DART: Noise Injection for Robust Imitation Learning"(CoRL 2017, arXiv:1703.09327)도
검증했으나 범위 조정을 위해 본문에서는 제외했다.

**검증 메모 (2026-09-11 추가):** 9절의 6개 항목은 웹 검색(ACM DL, NeurIPS 프로시딩, Springer 도서 페이지,
Crossref API)으로 제목·저자·게재처·연도·DOI를 확인했다. Bullo & Lewis는 출판사 표기 연도 2005(인쇄 2004-11)를
따랐다. Konidaris & Barto 2009는 NIPS 프로시딩 PDF로 확인했고 DOI는 없다. Winfree는 2판(2001)의 ISBN·DOI를 적었다.
