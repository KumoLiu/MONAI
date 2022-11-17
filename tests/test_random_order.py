# Copyright (c) MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from parameterized import parameterized
from test_one_of import InvA, InvB, NonInv

from monai.data import MetaTensor
from monai.transforms import EnsureChannelFirst, RandomOrder, TraceableTransform
from monai.transforms.compose import Compose

KEYS = ["x", "y"]
TEST_INVERSES = [
    (RandomOrder((InvA(KEYS), InvB(KEYS))), True, True),
    (Compose((RandomOrder((InvA(KEYS), InvB(KEYS))), RandomOrder((InvB(KEYS), InvA(KEYS))))), True, False),
    (RandomOrder((Compose((InvA(KEYS), InvB(KEYS))), Compose((InvB(KEYS), InvA(KEYS))))), True, False),
    (RandomOrder((NonInv(KEYS), NonInv(KEYS))), False, False),
]


class TestRandomOrder(unittest.TestCase):
    def test_flatten_and_len(self):
        x = EnsureChannelFirst()
        t1 = Compose([x, x, x, x, Compose([RandomOrder([x, x]), x, x])])

        t2 = t1.flatten()
        for t in t2.transforms:
            self.assertNotIsInstance(t, Compose)

        # test len
        self.assertEqual(len(t1), 8)

    @parameterized.expand(TEST_INVERSES)
    def test_inverse(self, transform, invertible, use_metatensor):
        data = {k: (i + 1) * 10.0 if not use_metatensor else MetaTensor((i + 1) * 10.0) for i, k in enumerate(KEYS)}
        fwd_data = transform(data)

        # call the inverse
        fwd_inv_data = transform.inverse(fwd_data)

        if invertible:
            for k in KEYS:
                # check transform was removed
                if not use_metatensor:
                    self.assertTrue(
                        len(fwd_inv_data[TraceableTransform.trace_key(k)])
                        < len(fwd_data[TraceableTransform.trace_key(k)])
                    )
                # check data is same as original (and different from forward)
                self.assertEqual(fwd_inv_data[k], data[k])
                self.assertNotEqual(fwd_inv_data[k], fwd_data[k])
        else:
            # if not invertible, should not change the data
            self.assertDictEqual(fwd_data, fwd_inv_data)


if __name__ == "__main__":
    unittest.main()
