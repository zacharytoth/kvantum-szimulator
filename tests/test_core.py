# #Q1 működése mockup adatokkal
# # FONTOS ugyanazzal a seedel az rng ugyanazt adja-e
# from bb84_core import Basis, Photon, SimConfig, SimState, Step, get_rng

# def test_Q1():
#     sc = SimConfig()
#     p1 = Photon(angle=0.0, symbol="->")
#     ss = SimState(config=sc, alice_bits=[0,1], photons=[p1])
#     rng1 = get_rng(42)
#     rng2 = get_rng(42)
#     assert rng1.randint(0, 100) == rng2.randint(0, 100)
#     assert ss.alice_bits == [0,1]
#     assert ss.photons == [p1]