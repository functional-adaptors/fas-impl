############################################################
#### Description:
# Our implementation of El Gamal Public Key Encryption.
# msg is encoded in the exponent while encrypting it. 

# Author: Nikhil Vanjani
############################################################

import time 
import pickle
import random
import multiprocessing as mp

from utils import *
import settings

# # Set DEBUG to True to get a detailed debug output including
# # intermediate values during key generation, signing, and
# # verification. This is implemented via calls to the
# # debug_print_vars(settings.DEBUG) function.
# #
# # If you want to print values on an individual basis, use
# # the pretty() function, e.g., print(pretty(foo)).
# DEBUG = True
# PS: DEBUG has been moved to settings.py

#### PKE Setup: returns pk, sk
def pke_setup(pkelen: int) -> (dict, dict):
    seckey = {}
    pubkey = {}
    for i in range(pkelen):
        # seckey_int_i = i+1
        seckey_int_i = random.randint(1,n-1)
        seckey_i = bytes_from_int(seckey_int_i)
        seckey[i] = seckey_i

    #### ==== This is parallel and gives almost same numbers as previous. Crucially, results are in order. ====
    # num CPUs 
    cpu_num = os.cpu_count()
    # print("PKE.Setup: check2: cpu_num: {}".format(cpu_num))
    parallel_st = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers = cpu_num, mp_context=mp.get_context('spawn'), max_tasks_per_child = pkelen) as executor:
        pubkey_list = list(executor.map(pubkey_gen, 
            (seckey[i] for i in range(pkelen)),
            ))
    for i in range(pkelen):
        pubkey[i] = pubkey_list[i]

    # print("sk time: {}, pk time: {}, parallel pk time: {}".format(sk_time, pk_time, parallel_time))
    # if pubkey != pubkey_new:
    #     print("PARALLEL FAILURE: pke setup")
    debug_print_vars(settings.DEBUG)
    return (pubkey, seckey)

## outputs seckey such that its each co-ordinate is same 
## outputs pubkey such that its each co-ordinate is same 
def pke_setup_dummy(pkelen: int) -> (dict, dict):
    seckey = {}
    pubkey = {}
    fixed_seckey = bytes_from_int(random.randint(1,n-1))
    fixed_pubkey = pubkey_gen(fixed_seckey)

    for i in range(pkelen):
        seckey[i] = fixed_seckey

    for i in range(pkelen):
        pubkey[i] = fixed_pubkey

    # print("sk time: {}, pk time: {}, parallel pk time: {}".format(sk_time, pk_time, parallel_time))
    # if pubkey != pubkey_new:
    #     print("PARALLEL FAILURE: pke setup")
    debug_print_vars(settings.DEBUG)
    return (pubkey, seckey)


def pke_setup_sequential(pkelen: int) -> (dict, dict):
    seckey = {}
    pubkey = {}
    for i in range(pkelen):
        # seckey_int_i = i+1
        seckey_int_i = random.randint(1,n-1)
        seckey_i = bytes_from_int(seckey_int_i)
        pubkey_i = pubkey_gen(seckey_i)
        seckey[i] = seckey_i
        pubkey[i] = pubkey_i

    debug_print_vars(settings.DEBUG)
    return (pubkey, seckey)

# def pke_encrypt_helper(i: int, pubkey: bytes, msg: int, r: int, ct1: list[bytes]):
def pke_encrypt_helper(i: int, pubkey: bytes, msg: int, r: int) -> bytes:
    pk_i = point_from_bytes(pubkey)
    if not is_point_on_curve(pk_i):
        raise ValueError('pke_encrypt: pk_{} must be a point on the elliptic curve.'.format(i))
    msg_i = point_mul(G, msg)
    ct1_i = point_add(msg_i, point_mul(pk_i, r))
    # ct1[i] = bytes_from_point(ct1_i)
    return bytes_from_point(ct1_i)

def pke_encrypt(pkelen: int, pubkey: dict, msg: dict) -> (bytes, dict):
    if len(pubkey) != pkelen:
        raise ValueError('pke_encrypt: The public key must be list of length: {}'.format(pkelen))
    if len(msg) != pkelen:
        # maybe append with zeros instead of raising error?
        raise ValueError('pke_encrypt: The message must be list of length: {}'.format(pkelen))

    r = random.randint(1, n-1)
    ct0 = bytes_from_point(point_mul(G, r))
        
    #### ==== This is parallel but does not give numbers better than sequential ====
    # ct1 = [None]* pkelen
    # with concurrent.futures.ThreadPoolExecutor(max_workers=pkelen) as executor:
    #     futures = [executor.submit(pke_encrypt_helper, i, pubkey[i], msg[i], r, ct1) for i in range(pkelen)]
    #     results = [future.result() for future in concurrent.futures.as_completed(futures)]

    #### ==== This is parallel and gives almost same numbers as previous. Crucially, results are in order. ====
    # num CPUs 
    cpu_num = os.cpu_count()
    # print("PKE.Enc: check2: cpu_num: {}".format(cpu_num))
    # print("Number of CPUs available: {}".format(cpu_num))
    # parallel_st = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers = cpu_num, mp_context=mp.get_context('spawn'), max_tasks_per_child = pkelen) as executor:
        ct1_list = list(executor.map(pke_encrypt_helper, 
            (i for i in range(pkelen)), 
            (pubkey[i] for i in range(pkelen)),
            (msg[i] for i in range(pkelen)),
            (r for i in range(pkelen))
            ))
    ct1 = {}
    for i in range(pkelen):
        ct1[i] = ct1_list[i]
    # parallel_et = time.time()
    # parallel_time = parallel_et - parallel_st
    # print("parallel enc time using map: {}".format(parallel_time))


    debug_print_vars(settings.DEBUG)
    return (ct0, ct1)

## Assumes each co-ordinate of pubkey is same 
## Assumes each co-ordinate of msg is same 
def pke_encrypt_dummy(pkelen: int, pubkey: dict, msg: dict) -> (bytes, dict):
    if len(pubkey) != pkelen:
        raise ValueError('pke_encrypt: The public key must be list of length: {}'.format(pkelen))
    if len(msg) != pkelen:
        # maybe append with zeros instead of raising error?
        raise ValueError('pke_encrypt: The message must be list of length: {}'.format(pkelen))

    r = random.randint(1, n-1)
    ct0 = bytes_from_point(point_mul(G, r))
        
    ct1 = {}
    dummy_ct1 = pke_encrypt_helper(0, pubkey[0], msg[0], r)
    for i in range(pkelen):
        ct1[i] = dummy_ct1

    debug_print_vars(settings.DEBUG)
    return (ct0, ct1)

## Assumes each co-ordinate of pubkey is same 
## Assumes first pkelen-1 co-ordinates of msg are same and last co-ordinate is zero.
def pke_encrypt_dummy_with_last_zero(pkelen: int, pubkey: dict, msg: dict) -> (bytes, dict):
    if len(pubkey) != pkelen:
        raise ValueError('pke_encrypt: The public key must be list of length: {}'.format(pkelen))
    if len(msg) != pkelen:
        # maybe append with zeros instead of raising error?
        raise ValueError('pke_encrypt: The message must be list of length: {}'.format(pkelen))

    r = random.randint(1, n-1)
    ct0 = bytes_from_point(point_mul(G, r))
        
    ct1 = {}
    dummy_ct1 = pke_encrypt_helper(0, pubkey[0], msg[0], r)
    for i in range(pkelen-1):
        ct1[i] = dummy_ct1
    ct1[pkelen-1] = pke_encrypt_helper(0, pubkey[pkelen-1], msg[pkelen-1], r)

    debug_print_vars(settings.DEBUG)
    return (ct0, ct1)


def pke_encrypt_sequential(pkelen: int, pubkey: dict, msg: dict) -> (bytes, dict):
    if len(pubkey) != pkelen:
        raise ValueError('pke_encrypt: The public key must be list of length: {}'.format(pkelen))
    if len(msg) != pkelen:
        # maybe append with zeros instead of raising error?
        raise ValueError('pke_encrypt: The message must be list of length: {}'.format(pkelen))

    r = random.randint(1, n-1)
    ct0 = bytes_from_point(point_mul(G, r))
    ct1 = {}
    time1 = 0
    time2 = 0
    for i in range(pkelen):        
        pk_i = point_from_bytes(pubkey[i])
        if not is_point_on_curve(pk_i):
            raise ValueError('pke_encrypt: pk_{} must be a point on the elliptic curve.'.format(i))
        t1_st = time.time()
        msg_i = point_mul(G, msg[i])
        t1_et = time.time()
        debug_print_vars(settings.DEBUG)
        ct1_i = point_add(msg_i, point_mul(pk_i, r))
        t2_et = time.time()
        time1 += t1_et - t1_st
        time2 += t2_et - t1_et
        ct1[i] = bytes_from_point(ct1_i)
    print('time1: {}, time2: {}'.format(time1, time2))        
    debug_print_vars(settings.DEBUG)
    return (ct0, ct1)

# def pke_decrypt_helper(i: int, seckey: bytes, ct0_point: Optional[Point], ct1: bytes, bound: int, msg_dict: dict) -> int:
def pke_decrypt_helper(i: int, seckey: bytes, ct0_point: Optional[Point], ct1: bytes, bound: int) -> int:
    # print('pke_decrypt: decrypting index {}...'.format(i))        
    sk_i = int_from_bytes(seckey)
    if not (1 <= sk_i <= n - 1):
        raise ValueError('pke_decrypt: sk_{} must be an integer in the range {1, ..., n-1}.'.format(i))

    # pk_i = point_from_bytes(pubkey)
    # if not is_point_on_curve(pk_i):
    #     raise ValueError('pke_decrypt: pk_{} must be a point on the elliptic curve.'.format(i))

    ct1_i = point_from_bytes(ct1)
    if not is_point_on_curve(ct1_i):
        raise ValueError('pke_decrypt: ct1_{} must be a point on the elliptic curve.'.format(i))

    local_msg_i = point_add(ct1_i, point_mul(ct0_point, n - sk_i))
    # found = False
    found = True
    # TODO: add check for not found
    # val_i = msg_dict[local_msg_i]
    val_i = compute_discrete_log(local_msg_i, bound)
    if not found:
        raise ValueError('pke_decrypt: msg_{} outside range {0, ..., bound-1}.'.format(i))
    return val_i

# def pke_decrypt(pkelen: int, seckey: list[bytes], ct0: bytes, ct1: list[bytes], bound: int, msg_dict: dict) -> list[int]:
def pke_decrypt(pkelen: int, seckey: dict, ct0: bytes, ct1: dict, bound: int) -> dict:
    # if len(pubkey) != pkelen:
    #     raise ValueError('pke_decrypt: The public key must be list of length: {}'.format(pkelen))
    if len(seckey) != pkelen:
        raise ValueError('pke_decrypt: The secret key must be list of length: {}'.format(pkelen))
    if len(ct0) != 64:
        raise ValueError('pke_decrypt: ct0 must be 64-bytes array')
    if len(ct1) != pkelen:
        raise ValueError('pke_decrypt: ct1 must be list of length: {}'.format(pkelen))

    ct0_point = point_from_bytes(ct0)
    if not is_point_on_curve(ct0_point):
        raise ValueError('pke_decrypt: ct0 must be a point on the elliptic curve.'.format(i))

    # num CPUs 
    cpu_num = os.cpu_count()
    # print("PKE.Dec: check2: cpu_num: {}".format(cpu_num))
    # print("Number of CPUs available: {}".format(cpu_num))

    #### ==== This is parallel but does not give numbers better than sequential ====
    # parallel_st = time.time()
    # MSG = [None]* pkelen
    # with concurrent.futures.ThreadPoolExecutor(max_workers = cpu_num) as executor:
    #     futures = [executor.submit(pke_decrypt_helper, i, pubkey[i], seckey[i], ct0_point, ct1[i], bound, msg_dict, MSG) for i in range(pkelen)]
    #     results = [future.result() for future in concurrent.futures.as_completed(futures)]
    # parallel_et = time.time()
    # parallel_time = parallel_et - parallel_st
    # print("parallel dec time type1: {}".format(parallel_time))

    #### ==== This is parallel and gives best numbers, but results maybe be out of order. If so, switch to map based option next ====
    # parallel_st = time.time()
    # with concurrent.futures.ProcessPoolExecutor(max_workers = cpu_num) as executor:
    #     futures = [executor.submit(pke_decrypt_helper, i, pubkey[i], seckey[i], ct0_point, ct1[i], bound, msg_dict) for i in range(pkelen)]
    #     results = [future.result() for future in futures]
    # parallel_et = time.time()
    # parallel_time = parallel_et - parallel_st
    # print("parallel dec time using submit: {}".format(parallel_time))

    #### ==== This is parallel and gives almost same numbers as previous. Crucially, results are in order. ====
    parallel_st = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers = cpu_num, mp_context=mp.get_context('spawn'), max_tasks_per_child = pkelen) as executor:
        results_list = list(executor.map(pke_decrypt_helper, 
            (i for i in range(pkelen)), 
            # (pubkey[i] for i in range(pkelen)),
            (seckey[i] for i in range(pkelen)),
            (ct0_point for i in range(pkelen)),
            (ct1[i] for i in range(pkelen)),
            (bound for i in range(pkelen)),
            # (msg_dict for i in range(pkelen)),
            ))
    parallel_et = time.time()
    parallel_time = parallel_et - parallel_st
    # print("parallel dec time using map: {}".format(parallel_time))
    # print("results: {}".format(results))

    #### ==== This is parallel and gives almost slightly worse running time that previous two. ====
    # parallel_st = time.time()
    # chunksize = max(1, pkelen // (4 * cpu_num))
    # with concurrent.futures.ProcessPoolExecutor(max_workers = cpu_num) as executor:
    #     results = list(executor.map(pke_decrypt_helper, 
    #         (i for i in range(pkelen)), 
    #         (pubkey[i] for i in range(pkelen)),
    #         (seckey[i] for i in range(pkelen)),
    #         (ct0_point for i in range(pkelen)),
    #         (ct1[i] for i in range(pkelen)),
    #         (bound for i in range(pkelen)),
    #         (msg_dict for i in range(pkelen)),
    #         chunksize = chunksize
    #         ))
    # parallel_et = time.time()
    # parallel_time = parallel_et - parallel_st
    # print("parallel dec time using map: {}, chunksize: {}".format(parallel_time, chunksize))


    # parallel_st = time.time()
    # args = []
    # for i in range(pkelen):
    #     args.append((i, pubkey[i], seckey[i], ct0_point, ct1[i], bound, msg_dict))
    # with multiprocessing.Pool(cpu_num) as executor:
    #     results = executor.starmap(pke_decrypt_helper, args)
    # parallel_et = time.time()
    # parallel_time = parallel_et - parallel_st
    # print("parallel dec time using Pool.map: {}".format(parallel_time))

    # if msg != MSG:
    #     print("msg: {}".format(msg))
    #     print("MSG: {}".format(MSG))
    #     print("PARALLEL FAILURE")
    # if msg != results:
    #     print("msg: {}".format(msg))
    #     print("results: {}".format(MSG))
    #     print("PARALLEL FAILURE ============")

    results = {}
    for i in range(pkelen):
        results[i] = results_list[i]
    debug_print_vars(settings.DEBUG)
    # return msg
    return results


# def pke_decrypt_sequential(pkelen: int, seckey: list[bytes], ct0: bytes, ct1: list[bytes], bound: int, msg_dict: dict) -> list[int]:
def pke_decrypt_sequential(pkelen: int, seckey: dict, ct0: bytes, ct1: dict, bound: int) -> dict:
    # if len(pubkey) != pkelen:
    #     raise ValueError('pke_decrypt: The public key must be list of length: {}'.format(pkelen))
    if len(seckey) != pkelen:
        raise ValueError('pke_decrypt: The secret key must be list of length: {}'.format(pkelen))
    if len(ct0) != 64:
        raise ValueError('pke_decrypt: ct0 must be 64-bytes array')
    if len(ct1) != pkelen:
        raise ValueError('pke_decrypt: ct1 must be list of length: {}'.format(pkelen))

    ct0_point = point_from_bytes(ct0)
    if not is_point_on_curve(ct0_point):
        raise ValueError('pke_decrypt: ct0 must be a point on the elliptic curve.'.format(i))

    msg = {}
    sequence_st = time.time()
    for i in range(pkelen):
        # print('pke_decrypt: decrypting index {}...'.format(i))        
        sk_i = int_from_bytes(seckey[i])
        if not (1 <= sk_i <= n - 1):
            raise ValueError('pke_decrypt: sk_{} must be an integer in the range {1, ..., n-1}.'.format(i))

        # pk_i = point_from_bytes(pubkey[i])
        # if not is_point_on_curve(pk_i):
        #     raise ValueError('pke_decrypt: pk_{} must be a point on the elliptic curve.'.format(i))

        ct1_i = point_from_bytes(ct1[i])
        if not is_point_on_curve(ct1_i):
            raise ValueError('pke_decrypt: ct1_{} must be a point on the elliptic curve.'.format(i))

        local_msg_i = point_add(ct1_i, point_mul(ct0_point, n - sk_i))
        # found = False
        found = True
        val_i = compute_discrete_log(local_msg_i, bound)
        # val_i = msg_dict[local_msg_i]
        # print('val_{}: {}'.format(i, val_i))
        msg[i] = val_i
        # for j in range(bound):
        #     if local_msg_i == point_mul(G, j):
        #         found = True 
        #         msg.append(j)
        if not found:
            raise ValueError('pke_decrypt: msg_{} outside range {0, ..., bound-1}.'.format(i))
    sequence_et = time.time()
    sequence_time = sequence_et - sequence_st
    # print("sequence dec time: {}".format(sequence_time))
    debug_print_vars(settings.DEBUG)
    return msg

def pke_decrypt_check(pkelen: int, pubkey: list[bytes], seckey: list[bytes], ct0: bytes, ct1: list[bytes], msg: list[int]) -> bool:
    if len(pubkey) != pkelen:
        raise ValueError('pke_decrypt_check: The public key must be list of length: {}'.format(pkelen))
    if len(seckey) != pkelen:
        raise ValueError('pke_decrypt_check: The secret key must be list of length: {}'.format(pkelen))
    if len(ct0) != 64:
        raise ValueError('pke_decrypt_check: ct0 must be 64-bytes array')
    if len(ct1) != pkelen:
        raise ValueError('pke_decrypt_check: ct1 must be list of length: {}'.format(pkelen))

    if len(msg) != pkelen:
        # maybe append with zeros instead of raising error?
        raise ValueError('pke_decrypt_check: The message must be list of length: {}'.format(pkelen))

    ct0_point = point_from_bytes(ct0)
    if not is_point_on_curve(ct0_point):
        raise ValueError('pke_decrypt_check: ct0 must be a point on the elliptic curve.'.format(i))

    for i in range(pkelen):
        print('pke_decrypt_check: checking index {}...'.format(i))        
        sk_i = int_from_bytes(seckey[i])
        if not (1 <= sk_i <= n - 1):
            raise ValueError('pke_decrypt_check: sk_{} must be an integer in the range {1, ..., n-1}.'.format(i))

        pk_i = point_from_bytes(pubkey[i])
        if not is_point_on_curve(pk_i):
            raise ValueError('pke_decrypt_check: pk_{} must be a point on the elliptic curve.'.format(i))

        msg_i = point_mul(G, msg[i])
        ct1_i = point_from_bytes(ct1[i])
        if not is_point_on_curve(ct1_i):
            raise ValueError('pke_decrypt_check: ct1_{} must be a point on the elliptic curve.'.format(i))

        local_msg_i = point_add(ct1_i, point_mul(ct0_point, n - sk_i))
        if msg_i != local_msg_i:
            debug_print_vars(settings.DEBUG)
            print('decryption failed for index: {}'.format(i))
            return False
    return True

if __name__ == '__main__':
    settings.init()

    len_range = (1, 10, 100, 1000, 10000)
    # len_range = (1, 10)
    bound_range = []
    bound_range.append(1000)
    # bound_range.append(10000)
    # bound_range = (100, 10000, 100000)
    # bound_range = (10 ** 3, 10 ** 6, 10 ** 9)

    # bound_max = max(bound_range)
    # msg_dict = {}
    # # tmp = point_mul(G, 0)
    # # msg_dict[tmp] = 0
    # dict_st = time.time()
    # with open('msg_dict.pkl', 'rb') as fp:
    #     msg_dict = pickle.load(fp)
    # # for i in range(1, bound_max):
    # #     tmp = point_add(tmp, G)
    # #     msg_dict[tmp] = i
    # # print(msg_dict)
    # dict_et = time.time()
    # dict_time = dict_et - dict_st
    # print('DictTime: {}'.format(dict_time))

    test_enc_only = True

    for pkelen in len_range:
        for bound in bound_range:
            # count_add = 0
            # count_mul = 0

            msg = {}
            for i in range(pkelen):
                # msg_i = i+1
                # msg_i = random.randint(0, 2)
                msg_i = random.randint(0, bound-1)
                msg[i] = msg_i


            st = time.time()

            setup_st = time.time()
            (pubkey, seckey) = pke_setup(pkelen)
            # (pubkey, seckey) = pke_setup_sequential(pkelen)
            setup_et = time.time()
            setup_time = setup_et - setup_st
            try:
                enc_st = time.time()
                (ct0, ct1) = pke_encrypt(pkelen, pubkey, msg)
                # (ct0, ct1) = pke_encrypt_sequential(pkelen, pubkey, msg)
                enc_et = time.time()
                enc_time = enc_et - enc_st
                if not test_enc_only:
                    try:
                        dec_st = time.time()
                        val = pke_decrypt(pkelen, seckey, ct0, ct1, bound)
                        # val = pke_decrypt_sequential(pkelen, seckey, ct0, ct1, bound)
                        dec_et = time.time()
                        dec_time = dec_et - dec_st
                        # print('msg encrpted: {}'.format(msg))
                        # print('msg decrpted: {}'.format(val))
                        if val != msg:
                            print('pke_decrypt test FAILED')
                        # else: 
                        #     print('SUCCESS')
                        # ret = pke_decrypt_check(pkelen, pubkey, seckey, ct0, ct1, msg)
                        # print(ret)
                        et = time.time()
                        elapsed_time = et - st 
                        print('pkelen: {} \t bound: {} \t ExecTime: {:.3f} \t SetupTime: {:.3f} \t EncTime: {:.3f} \t DecTime: {:.3f}'.format(pkelen, bound, elapsed_time, setup_time, enc_time, dec_time))
                        # print('pkelen: {} \t bound: {} \t ExecutionTime: {} \t SetupTime: {} \t EncTime: {} \t DecTime: {} \t countAdd: {} \t countMul: {}'.format(pkelen, bound, elapsed_time, setup_time, enc_time, dec_time, count_add, count_mul))

                    except RuntimeError as e:
                        print(' * pke_decrypt test raised exception:', e)
                        # print(' * pke_decrypt_check test raised exception:', e)

            except RuntimeError as e:
                print(' * pke_encrypt test raised exception:', e)
            

            et = time.time()
            elapsed_time = et - st 
            print('pkelen: {} \t bound: {} \t ExecTime: {:.3f} \t SetupTime: {:.3f} \t EncTime: {:.3f}'.format(pkelen, bound, elapsed_time, setup_time, enc_time))



