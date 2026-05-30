"""
2026-05-30
fflate python实现, 请勿将该功能更改为gzip或zlib等其他压缩算法, 以免导致加密结果不一致
"""

import math
import struct
import time
import zlib


FLEB = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0, 0, 0, 0]
FDEB = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 0, 0]
CLIM = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]
DEO = [65540, 131080, 131088, 131104, 262176, 1048704, 1048832, 2114560, 2117632]
ET = []


def _freb(eb, start):
    b = [0] * 31
    for i in range(31):
        b[i] = start = start + (1 << eb[i - 1])
    r = [0] * b[30]
    for i in range(1, 30):
        for j in range(b[i], b[i + 1]):
            r[j] = ((j - b[i]) << 5) | i
    return b, r


FL, REVFL = _freb(FLEB, 2)
FL[28] = 258
if len(REVFL) <= 258:
    REVFL.extend([0] * (259 - len(REVFL)))
REVFL[258] = 28
FD, REVFD = _freb(FDEB, 0)

REV = [0] * 32768
for _i in range(32768):
    _x = ((_i & 0xAAAA) >> 1) | ((_i & 0x5555) << 1)
    _x = ((_x & 0xCCCC) >> 2) | ((_x & 0x3333) << 2)
    _x = ((_x & 0xF0F0) >> 4) | ((_x & 0x0F0F) << 4)
    REV[_i] = (((_x & 0xFF00) >> 8) | ((_x & 0x00FF) << 8)) >> 1


def _hmap(cd, mb, r):
    s = len(cd)
    l = [0] * mb
    for v in cd:
        if v:
            l[v - 1] += 1
    le = [0] * mb
    for i in range(1, mb):
        le[i] = (le[i - 1] + l[i - 1]) << 1
    if r:
        co = [0] * (1 << mb)
        rvb = 15 - mb
        for i, clen in enumerate(cd):
            if clen:
                sv = (i << 4) | clen
                rb = mb - clen
                v = le[clen - 1] << rb
                le[clen - 1] += 1
                end = v | ((1 << rb) - 1)
                while v <= end:
                    co[REV[v] >> rvb] = sv
                    v += 1
    else:
        co = [0] * s
        for i, clen in enumerate(cd):
            if clen:
                co[i] = REV[le[clen - 1]] >> (15 - clen)
                le[clen - 1] += 1
    return co


FLT = [0] * 288
for _i in range(144):
    FLT[_i] = 8
for _i in range(144, 256):
    FLT[_i] = 9
for _i in range(256, 280):
    FLT[_i] = 7
for _i in range(280, 288):
    FLT[_i] = 8
FDT = [5] * 32
FLM = _hmap(FLT, 9, 0)
FDM = _hmap(FDT, 5, 0)


def _shft(p):
    return (p + 7) // 8


def _wbits(d, p, v):
    v <<= p & 7
    o = p // 8
    d[o] = (d[o] | v) & 255
    d[o + 1] = (d[o + 1] | (v >> 8)) & 255


def _wbits16(d, p, v):
    v <<= p & 7
    o = p // 8
    d[o] = (d[o] | v) & 255
    d[o + 1] = (d[o + 1] | (v >> 8)) & 255
    d[o + 2] = (d[o + 2] | (v >> 16)) & 255


def _ln(n, lengths, depth):
    if n["s"] == -1:
        return max(_ln(n["l"], lengths, depth + 1), _ln(n["r"], lengths, depth + 1))
    lengths[n["s"]] = depth
    return depth


def _htree(freq, mb):
    t = [{"s": i, "f": f} for i, f in enumerate(freq) if f]
    s = len(t)
    t2 = [dict(x) for x in t]
    if not s:
        return {"t": ET, "l": 0}
    if s == 1:
        v = [0] * (t[0]["s"] + 1)
        v[t[0]["s"]] = 1
        return {"t": v, "l": 1}
    t.sort(key=lambda x: x["f"])
    t.append({"s": -1, "f": 25001})
    l, rr = t[0], t[1]
    i0, i1, i2 = 0, 1, 2
    t[0] = {"s": -1, "f": l["f"] + rr["f"], "l": l, "r": rr}
    while i1 != s - 1:
        if t[i0]["f"] < t[i2]["f"]:
            l = t[i0]
            i0 += 1
        else:
            l = t[i2]
            i2 += 1
        if i0 != i1 and t[i0]["f"] < t[i2]["f"]:
            rr = t[i0]
            i0 += 1
        else:
            rr = t[i2]
            i2 += 1
        t[i1] = {"s": -1, "f": l["f"] + rr["f"], "l": l, "r": rr}
        i1 += 1
    max_sym = max(x["s"] for x in t2)
    tr = [0] * (max_sym + 1)
    mbt = _ln(t[i1 - 1], tr, 0)
    if mbt > mb:
        i = 0
        dt = 0
        lft = mbt - mb
        cst = 1 << lft
        t2.sort(key=lambda a: (-tr[a["s"]], a["f"]))
        while i < s:
            sym = t2[i]["s"]
            if tr[sym] > mb:
                dt += cst - (1 << (mbt - tr[sym]))
                tr[sym] = mb
                i += 1
            else:
                break
        dt >>= lft
        while dt > 0:
            sym = t2[i]["s"]
            if tr[sym] < mb:
                dt -= 1 << (mb - tr[sym] - 1)
                tr[sym] += 1
            else:
                i += 1
        while i >= 0 and dt:
            sym = t2[i]["s"]
            if tr[sym] == mb:
                tr[sym] -= 1
                dt += 1
            i -= 1
        mbt = mb
    return {"t": tr, "l": mbt}


def _lc(c):
    s = len(c)
    while s and not c[s - 1]:
        s -= 1
    cl = []
    if s == 0:
        return {"c": cl, "n": 0}
    cln = c[0]
    cls = 1

    def w(v):
        cl.append(v)

    for i in range(1, s + 1):
        cur = c[i] if i < len(c) else None
        if cur == cln and i != s:
            cls += 1
        else:
            if not cln and cls > 2:
                while cls > 138:
                    w(32754)
                    cls -= 138
                if cls > 2:
                    w(((cls - 11) << 5) | 28690 if cls > 10 else ((cls - 3) << 5) | 12305)
                    cls = 0
            elif cls > 3:
                w(cln)
                cls -= 1
                while cls > 6:
                    w(8304)
                    cls -= 6
                if cls > 2:
                    w(((cls - 3) << 5) | 8208)
                    cls = 0
            while cls:
                w(cln)
                cls -= 1
            cls = 1
            cln = cur
    return {"c": cl, "n": s}


def _clen(cf, cl):
    return sum(cf[i] * (cl[i] if i < len(cl) else 0) for i in range(len(cf)))


def _wfblk(out, pos, dat):
    s = len(dat)
    o = _shft(pos + 2)
    out[o] = s & 255
    out[o + 1] = s >> 8
    out[o + 2] = out[o] ^ 255
    out[o + 3] = out[o + 1] ^ 255
    out[o + 4 : o + 4 + s] = dat
    return (o + 4 + s) * 8


def _wblk(dat, out, final, syms, lf, df, eb, li, bs, bl, p):
    _wbits(out, p, final)
    p += 1
    lf[256] += 1
    ht = _htree(lf, 15)
    dlt, mlb = ht["t"], ht["l"]
    ht = _htree(df, 15)
    ddt, mdb = ht["t"], ht["l"]
    lco = _lc(dlt)
    lclt, nlc = lco["c"], lco["n"]
    lco = _lc(ddt)
    lcdt, ndc = lco["c"], lco["n"]
    lcfreq = [0] * 19
    for x in lclt:
        lcfreq[x & 31] += 1
    for x in lcdt:
        lcfreq[x & 31] += 1
    ht = _htree(lcfreq, 7)
    lct, mlcb = ht["t"], ht["l"]
    nlcc = 19
    while nlcc > 4 and not (lct[CLIM[nlcc - 1]] if CLIM[nlcc - 1] < len(lct) else 0):
        nlcc -= 1
    flen = (bl + 5) << 3
    ftlen = _clen(lf, FLT) + _clen(df, FDT) + eb
    dtlen = _clen(lf, dlt) + _clen(df, ddt) + eb + 14 + 3 * nlcc + _clen(lcfreq, lct) + 2 * lcfreq[16] + 3 * lcfreq[17] + 7 * lcfreq[18]
    if bs >= 0 and flen <= ftlen and flen <= dtlen:
        return _wfblk(out, p, dat[bs : bs + bl])
    _wbits(out, p, 1 + (1 if dtlen < ftlen else 0))
    p += 2
    if dtlen < ftlen:
        lm, ll, dm, dl = _hmap(dlt, mlb, 0), dlt, _hmap(ddt, mdb, 0), ddt
        llm = _hmap(lct, mlcb, 0)
        _wbits(out, p, nlc - 257)
        _wbits(out, p + 5, ndc - 1)
        _wbits(out, p + 10, nlcc - 4)
        p += 14
        for i in range(nlcc):
            _wbits(out, p + 3 * i, lct[CLIM[i]] if CLIM[i] < len(lct) else 0)
        p += 3 * nlcc
        for clct in (lclt, lcdt):
            for val in clct:
                length = val & 31
                _wbits(out, p, llm[length])
                p += lct[length]
                if length > 15:
                    _wbits(out, p, (val >> 5) & 127)
                    p += val >> 12
    else:
        lm, ll, dm, dl = FLM, FLT, FDM, FDT
    for i in range(li):
        sym = syms[i]
        if sym > 255:
            length = (sym >> 18) & 31
            _wbits16(out, p, lm[length + 257])
            p += ll[length + 257]
            if length > 7:
                _wbits(out, p, (sym >> 23) & 31)
                p += FLEB[length]
            dst = sym & 31
            _wbits16(out, p, dm[dst])
            p += dl[dst]
            if dst > 3:
                _wbits16(out, p, (sym >> 5) & 8191)
                p += FDEB[dst]
        else:
            _wbits16(out, p, lm[sym])
            p += ll[sym]
    _wbits16(out, p, lm[256])
    return p + ll[256]


def _dflt(dat, lvl=6, plvl=None, pre=0, post=0):
    dat = bytes(dat)
    s = len(dat)
    if plvl is None:
        plvl = math.ceil(max(8, min(13, math.log(s))) * 1.5) if s else 12
    out = bytearray(pre + s + 5 * (1 + math.ceil(s / 7000)) + post)
    w = memoryview(out)[pre : len(out) - post]
    pos = 0
    if lvl:
        opt = DEO[lvl - 1]
        n, chain = opt >> 13, opt & 8191
        msk = (1 << plvl) - 1
        prev = [0] * 32768
        head = [0] * (msk + 1)
        bs1 = math.ceil(plvl / 3)
        bs2 = 2 * bs1

        def get(idx):
            return dat[idx] if 0 <= idx < s else 0

        def hsh(idx):
            return (get(idx) ^ (get(idx + 1) << bs1) ^ (get(idx + 2) << bs2)) & msk

        syms = [0] * 25000
        lf = [0] * 288
        df = [0] * 32
        literal_count = eb = i = li = wi = bs = 0
        while i + 2 < s:
            hv = hsh(i)
            imod = i & 32767
            pimod = head[hv]
            prev[imod] = pimod
            head[hv] = imod
            if wi <= i:
                rem = s - i
                if (literal_count > 7000 or li > 24576) and rem > 423:
                    pos = _wblk(dat, w, 0, syms, lf, df, eb, li, bs, i - bs, pos)
                    li = literal_count = eb = 0
                    bs = i
                    for j in range(286):
                        lf[j] = 0
                    for j in range(30):
                        df[j] = 0
                l = 2
                d = 0
                ch = chain
                dif = (imod - pimod) & 32767
                if rem > 2 and hv == hsh(i - dif):
                    maxn = min(n, rem) - 1
                    maxd = min(32767, i)
                    ml = min(258, rem)
                    while dif <= maxd and ch - 1 and imod != pimod:
                        ch -= 1
                        if dat[i + l] == dat[i + l - dif]:
                            nl = 0
                            while nl < ml and dat[i + nl] == dat[i + nl - dif]:
                                nl += 1
                            if nl > l:
                                l = nl
                                d = dif
                                if nl > maxn:
                                    break
                                mmd = min(dif, nl - 2)
                                md = 0
                                for j in range(mmd):
                                    ti = (i - dif + j) & 32767
                                    pti = prev[ti]
                                    cd = (ti - pti) & 32767
                                    if cd > md:
                                        md = cd
                                        pimod = ti
                        imod = pimod
                        pimod = prev[imod]
                        dif += (imod - pimod) & 32767
                if d:
                    syms[li] = 268435456 | (REVFL[l] << 18) | REVFD[d]
                    li += 1
                    lin, din = REVFL[l] & 31, REVFD[d] & 31
                    eb += FLEB[lin] + FDEB[din]
                    lf[257 + lin] += 1
                    df[din] += 1
                    wi = i + l
                    literal_count += 1
                else:
                    syms[li] = dat[i]
                    li += 1
                    lf[dat[i]] += 1
            i += 1
        i = max(i, wi)
        while i < s:
            syms[li] = dat[i]
            li += 1
            lf[dat[i]] += 1
            i += 1
        pos = _wblk(dat, w, 1, syms, lf, df, eb, li, bs, i - bs, pos)
    else:
        i = 0
        while i < s + 1:
            e = i + 65535
            if e >= s:
                w[pos // 8] = 1
                e = s
            pos = _wfblk(w, pos + 1, dat[i:e])
            i += 65535
    return bytes(out[: pre + _shft(pos) + post])


def gzip_sync(data, level=6, mtime=None):
    data = bytes(data)
    if mtime is None:
        mtime = int(time.time())
    out = bytearray(_dflt(data, lvl=level, pre=10, post=8))
    out[0] = 31
    out[1] = 139
    out[2] = 8
    out[8] = 4 if level < 2 else 2 if level == 9 else 0
    out[9] = 3
    if mtime != 0:
        out[4:8] = struct.pack("<I", int(mtime))
    out[-8:-4] = struct.pack("<I", zlib.crc32(data) & 0xFFFFFFFF)
    out[-4:] = struct.pack("<I", len(data) & 0xFFFFFFFF)
    return bytes(out)
