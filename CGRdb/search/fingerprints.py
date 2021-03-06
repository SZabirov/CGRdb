# -*- coding: utf-8 -*-
#
#  Copyright 2017-2019 Ramil Nugmanov <stsouko@live.ru>
#  Copyright 2018, 2019 Adelia Fatykhova <adelik21979@gmail.com>
#  This file is part of CGRdb.
#
#  CGRdb is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
from CachedMethods import cached_property
from hashlib import md5
from CGRtools.containers import ReactionContainer
from CIMtools.exceptions import ConfigurationError
from CIMtools.preprocessing import Fragmentor
from numpy import zeros


class Fingerprint:
    @cached_property
    def fingerprint(self):
        x = zeros(2 ** self._fp_size, dtype=bool)
        x[self.bit_array] = True
        return x

    _fp_size = 12
    _fp_count = 4
    _fp_active = 2
    _fragmentor_version = '2017.x'
    _fragmentor_workpath = '/tmp'


class FingerprintMolecule(Fingerprint):
    @classmethod
    def get_fingerprint(cls, structure):
        mask = 2 ** cls._fp_size - 1
        fp_count = cls._fp_count
        fp_active = cls._fp_active * 2
        bits_map = {}
        active_bits = set()

        for i in set(int(a) for _, a in structure.atoms()):
            active_bits.add(i >> 12)
            active_bits.add(i & mask)

        try:
            df = Fragmentor(version=cls._fragmentor_version, header=False, fragment_type=cls._fragment_type,
                            workpath=cls._fragmentor_workpath, min_length=cls._fragment_min,
                            max_length=cls._fragment_max, useformalcharge=True).transform([structure])
        except ConfigurationError:
            return active_bits

        for f in df.columns:
            prev = []
            for i in range(1, fp_count + 1):
                bs = md5(f'{i}_{f}'.encode()).digest()
                bits_map[(f, i)] = prev = [int.from_bytes(bs[r: r + 2], 'big') & mask
                                           for r in range(0, fp_active, 2)] + prev

        for k, v in df.loc[0].items():
            if v:
                active_bits.update(bits_map[(k, v if v < fp_count else fp_count)])
        return active_bits

    _fragment_type = 3
    _fragment_min = 2
    _fragment_max = 5


class FingerprintReaction(Fingerprint):
    @classmethod
    def get_fingerprint(cls, structure):
        if isinstance(structure, ReactionContainer):
            structure = ~structure
        try:
            df = Fragmentor(version=cls._fragmentor_version, header=False, fragment_type=cls._fragment_type,
                            workpath=cls._fragmentor_workpath, min_length=cls._fragment_min,
                            max_length=cls._fragment_max, cgr_dynbonds=cls._fragment_dynbond,
                            useformalcharge=True).transform([structure])
        except ConfigurationError:
            return set()

        mask = 2 ** cls._fp_size - 1
        fp_count = cls._fp_count
        fp_active = cls._fp_active * 2
        bits_map = {}

        for f in df.columns:
            prev = []
            for i in range(1, fp_count + 1):
                bs = md5(f'{i}_{f}'.encode()).digest()
                bits_map[(f, i)] = prev = [int.from_bytes(bs[r: r + 2], 'big') & mask
                                           for r in range(0, fp_active, 2)] + prev
        active_bits = set()
        for k, v in df.loc[0].items():
            if v:
                active_bits.update(bits_map[(k, v if v < fp_count else fp_count)])
        return active_bits

    _fragment_type = 3
    _fragment_min = 2
    _fragment_max = 5
    _fragment_dynbond = 1


__all__ = ['FingerprintMolecule', 'FingerprintReaction']
