from custom_literals import *

import unittest

class TestLiteral(unittest.TestCase):
    def run_multiple_hooks(self, number):
        import itertools
        for combination in itertools.combinations(ALLOWED_TARGETS, number):
            with self.subTest(combination=combination):
                def foo(self):
                    return "correct"

                literal(*combination)(foo)
                try:
                    for target in combination:
                        self.assert_(hasattr(target, "foo"), f"target hook failed for {target}")
                    
                    target_type = lambda target: target if isinstance(target, type) else type(target)
                    combination_types = tuple(map(target_type, combination))
                    for other in set(ALLOWED_TARGETS) - set(combination):
                        if not issubclass(target_type(other), combination_types):
                            self.assert_(not hasattr(other, "foo"), f"types {other} affected by hooks on {combination}")
                # otherwise the other tests are affected
                # (because builtins are shared)
                finally:
                    for target in combination:
                        unliteral(target, "foo")

                for other in ALLOWED_TARGETS:
                    if other in combination:
                        self.assert_(not hasattr(other, "foo"), f"unhooking target {other} failed")
                    else:
                        self.assert_(not hasattr(other, "foo"), f"unhooking {combination} affected type {other}")
                
    def test_single_literal_hook(self):
        self.run_multiple_hooks(1)

    def test_many_literal_hooks(self):
        for n in range(2, 5):
            self.run_multiple_hooks(n)
    
    def test_str(self):
        @literal(str)
        def foo_str(self):
            return "correct"
        
        try:
            self.assertEqual("aa".foo_str, "correct", "str hook failed")
        finally:
            unliteral(str, "foo_str")

        with self.assertRaises(AttributeError, msg="str unhook failed"):
            "aa".foo_str
    
    def test_none(self):
        @literal(None)
        def foo_none(self):
            return "correct"
        try:
            self.assertEqual(None.foo_none, "correct", "none hook failed")

        finally:
            unliteral(None, "foo_none")
        with self.assertRaises(AttributeError, msg="none unhook failed"):
            None.foo_none

    def test_int_bool(self):
        @literal(int)
        def foo_int(self):
            return "correct"
        
        try:
            self.assertEqual((1).foo_int, "correct", "int hook failed")
            with self.assertRaises(AttributeError, msg="int hook affects bool"):
                True.foo_int
            
        finally:
            unliteral(int, "foo_int")

        @literal(int, bool)
        def foo_int_bool(self):
            return "true"
        
        self.assertEqual((1).foo_int_bool, "true", "int rehook failed")
        self.assertEqual(False.foo_int_bool, "true", "int+bool hook failed")
        unliteral(int, "foo_int_bool")
        unliteral(bool, "foo_int_bool")

        with self.assertRaises(AttributeError, msg="int unhook failed"):
            (0).foo_int_bool
        
        with self.assertRaises(AttributeError, msg="bool unhook failed"):
            False.foo_int_bool

    def test_float(self):
        @literal(float)
        def foo_float(self):
            return "correct"
        
        try:
            self.assertEqual((1.0).foo_float, "correct", "float hook failed")
        finally:
            unliteral(float, "foo_float")

        with self.assertRaises(AttributeError, msg="float unhook failed"):
            (0.0).foo_float
    
    def test_complex(self):
        @literal(complex)
        def foo_complex(self):
            return "correct"
        
        try:
            self.assertEqual((1j).foo_complex, "correct", "complex hook failed")
        finally:
            unliteral(complex, "foo_complex")

        with self.assertRaises(AttributeError, msg="complex unhook failed"):
            (0j).foo_complex
    
    def test_literally(self):
        from datetime import datetime
        try:
            with literally(int, unix=datetime.fromtimestamp):
                self.assertEqual((1647804818).unix, datetime(2022, 3, 20, 21, 33, 38), "context manager hook failed")
        
            with self.assertRaises(AttributeError, msg="context manager unhook failed"):
                (0).unix
        
        finally:
            try:
                unliteral(int, "unix")
            except AttributeError:
                pass # Already unhooked


    def test_class_based(self):
        try:
            @literals(str)
            class Foo:
                def bar(self):
                    return "correct"

            self.assertEqual("aa".bar, "correct", "class based hook failed")
            
        finally:
            unliteral(str, "bar")

        with self.assertRaises(AttributeError, msg="class based unhook failed"):
            "aa".bar
        
    def test_renamed_class_literal(self):
        try:
            @literals(str)
            class Foo:
                @rename("bar")
                def bees(self):
                    return "correct"
            
            self.assertEqual("aa".bar, "correct", "renamed class based hook failed")

        finally:
            unliteral(str, "bar")

        with self.assertRaises(AttributeError, msg="renamed class based unhook failed"):
            "aa".bar

    def test_class_multiple_targets(self):
        try:
            @literals(str, int)
            class Foo:
                def bar(self):
                    return "correct"

            self.assertEqual("aa".bar, "correct", "class based hook failed")
            self.assertEqual((1).bar, "correct", "class based hook failed")
            
        finally:
            unliteral(str, "bar")
            unliteral(int, "bar")

        with self.assertRaises(AttributeError, msg="class based unhook failed"):
            "aa".bar
        with self.assertRaises(AttributeError, msg="class based unhook failed"):
            (1).bar

    def test_class_multiple_literals(self):
        try:
            @literals(str)
            class CaseLiterals:
                @rename("u")
                def uppercase(self):
                    return self.upper()
                @rename("l")
                def lowercase(self):
                    return self.lower()
            
            self.assertEqual("aa".u, "AA", "class based hook failed")
            self.assertEqual("AA".l, "aa", "class based hook failed")

        finally:
            unliteral(str, "u")
            unliteral(str, "l")

    def test_class_with_lie(self):
        try:
            @literals(str)
            class Foo(lie(str)):
                @rename("bar")
                def bees(self):
                    return "correct"
            
            self.assertEqual("aa".bar, "correct", "renamed class based hook failed")

        finally:
            unliteral(str, "bar")

        with self.assertRaises(AttributeError, msg="renamed class based unhook failed"):
            "aa".bar

    def test_tuple(self):
        @literal(tuple)
        def bar_tuple(self):
            return "correct"
        
        try:
            self.assertEqual((1, 2).bar_tuple, "correct", "tuple hook failed")
        finally:
            unliteral(tuple, "bar_tuple")

        with self.assertRaises(AttributeError, msg="tuple unhook failed"):
            (1, 2).bar_tuple

    def test_strict_list(self):
        @literal(list, strict=True)
        def bar_list(self):
            return "correct"
        
        try:
            self.assertEqual([1, 2].bar_list, "correct", "list hook failed")
        finally:
            unliteral(list, "bar_list")

        with self.assertRaises(AttributeError, msg="list unhook failed"):
            [1, 2].bar_list
    
    def test_strict_listcomp(self):
        @literal(list, strict=True)
        def bar_list(self):
            return "correct"
        
        try:
            self.assertEqual([x for x in [1, 2]].bar_list, "correct", "listcomp hook failed")
        finally:
            unliteral(list, "bar_list")

        with self.assertRaises(AttributeError, msg="list unhook failed"):
            [x for x in [1, 2]].bar_list
    
    def test_list(self):
        @literal(list)
        def bar_list(self):
            return "correct"
        
        try:
            self.assertEqual([1, 2].bar_list, "correct", "list hook failed")
        finally:
            unliteral(list, "bar_list")

        with self.assertRaises(AttributeError, msg="list unhook failed"):
            [1, 2].bar_list
        
    def test_listcomp(self):
        @literal(list)
        def bar_list(self):
            return "correct"
        
        try:
            self.assertEqual([x for x in [1, 2]].bar_list, "correct", "listcomp hook failed")
        finally:
            unliteral(list, "bar_list")

        with self.assertRaises(AttributeError, msg="list unhook failed"):
            [x for x in [1, 2]].bar_list

    def test_strict_dict(self):
        @literal(dict, strict=True)
        def bar_dict(self):
            return "correct"
        
        try:
            self.assertEqual({1: 2}.bar_dict, "correct", "dict hook failed")
        finally:
            unliteral(dict, "bar_dict")

        with self.assertRaises(AttributeError, msg="dict unhook failed"):
            {1: 2}.bar_dict
    
    def test_strict_dictcomp(self):
        @literal(dict, strict=True)
        def bar_dict(self):
            return "correct"
        
        try:
            self.assertEqual({x: x for x in [1, 2]}.bar_dict, "correct", "dictcomp hook failed")
        finally:
            unliteral(dict, "bar_dict")

        with self.assertRaises(AttributeError, msg="dict unhook failed"):
            {x: x for x in [1, 2]}.bar_dict

    def test_dict(self):
        @literal(dict)
        def bar_dict(self):
            return "correct"
        
        try:
            self.assertEqual({1: 2}.bar_dict, "correct", "dict hook failed")
        finally:
            unliteral(dict, "bar_dict")

        with self.assertRaises(AttributeError, msg="dict unhook failed"):
            {1: 2}.bar_dict

    def test_dictcomp(self):
        @literal(dict)
        def bar_dict(self):
            return "correct"
        
        try:
            self.assertEqual({x: x for x in [1, 2]}.bar_dict, "correct", "dictcomp hook failed")
        finally:
            unliteral(dict, "bar_dict")

        with self.assertRaises(AttributeError, msg="dict unhook failed"):
            {x: x for x in [1, 2]}.bar_dict

    def test_strict_set(self):
        @literal(set, strict=True)
        def bar_set(self):
            return "correct"
        
        try:
            self.assertEqual({1, 2}.bar_set, "correct", "set hook failed")
        finally:
            unliteral(set, "bar_set")

        with self.assertRaises(AttributeError, msg="set unhook failed"):
            {1, 2}.bar_set

    def test_strict_setcomp(self):
        @literal(set, strict=True)
        def bar_set(self):
            return "correct"
        
        try:
            self.assertEqual({x for x in [1, 2]}.bar_set, "correct", "setcomp hook failed")
        finally:
            unliteral(set, "bar_set")

        with self.assertRaises(AttributeError, msg="set unhook failed"):
            {x for x in [1, 2]}.bar_set

    def test_set(self):
        @literal(set)
        def bar_set(self):
            return "correct"
        
        try:
            self.assertEqual({1, 2}.bar_set, "correct", "set hook failed")
        finally:
            unliteral(set, "bar_set")

        with self.assertRaises(AttributeError, msg="set unhook failed"):
            {1, 2}.bar_set

    def test_setcomp(self):
        @literal(set)
        def bar_set(self):
            return "correct"
        
        try:
            self.assertEqual({x for x in [1, 2]}.bar_set, "correct", "setcomp hook failed")
        finally:
            unliteral(set, "bar_set")

        with self.assertRaises(AttributeError, msg="set unhook failed"):
            {x for x in [1, 2]}.bar_set

    def test_variable_suffix(self):
        @literal(int, strict=True)
        def not_for_variables(self):
            return 0
        
        with self.assertRaises(TypeError, msg="variable suffixes not properly disallowed"):
            x = 1
            x.not_for_variables
        
        unliteral(int, "not_for_variables")

    def test_non_strict(self):
        @literal(int)
        def not_strict(self):
            return True

        try:
            x = 1
            self.assertTrue(x.not_strict, "non strict access failed, was too strict")    
        finally:
            unliteral(int, "not_strict")
        
    def test_fstring(self):
        @literal(str)
        def bar_str(self):
            return "correct"
        
        try:
            self.assertEqual(f"{1}".bar_str, "correct", "fstring hook failed")
        finally:
            unliteral(str, "bar_str")

        with self.assertRaises(AttributeError, msg="fstring unhook failed"):
            f"{1}".bar_str

    def test_tuple_non_const_strict(self):
        @literal(tuple, strict=True)
        def bar_tuple(self):
            return "correct"
        
        x = 1
        y = 2
        try:
            self.assertEqual((x, y).bar_tuple, "correct", "tuple hook failed")
        finally:
            unliteral(tuple, "bar_tuple")

        with self.assertRaises(AttributeError, msg="tuple unhook failed"):
            (x, y).bar_tuple

    def test_list_unpack_strict(self):
        @literal(list, strict=True)
        def bar_list(self):
            return "correct"
        
        a = [1, 2, 3]
        b = [4, 5, 6]
        try:
            self.assertEqual([*a, *b].bar_list, "correct", "list hook failed")
        finally:
            unliteral(list, "bar_list")

        with self.assertRaises(AttributeError, msg="list unhook failed"):
            [*a, *b].bar_list

    def test_tuple_unpack_strict(self):
        @literal(tuple, strict=True)
        def bar_tuple(self):
            return "correct"
        
        a = (1, 2, 3)
        b = (4, 5, 6)
        try:
            self.assertEqual((*a, *b).bar_tuple, "correct", "tuple hook failed")
        finally:
            unliteral(tuple, "bar_tuple")

        with self.assertRaises(AttributeError, msg="tuple unhook failed"):
            (*a, *b).bar_tuple
    
    def test_set_unpack_strict(self):
        @literal(set, strict=True)
        def bar_set(self):
            return "correct"
        
        a = {1, 2, 3}
        b = {4, 5, 6}
        try:
            self.assertEqual({*a, *b}.bar_set, "correct", "set hook failed")
        finally:
            unliteral(set, "bar_set")

        with self.assertRaises(AttributeError, msg="set unhook failed"):
            {*a, *b}.bar_set
    
    def test_dict_unpack_strict(self):
        @literal(dict, strict=True)
        def bar_dict(self):
            return "correct"
        
        a = {1: 1, 2: 2, 3: 3}
        b = {4: 4, 5: 5, 6: 6}
        try:
            self.assertEqual({**a, **b}.bar_dict, "correct", "dict hook failed")
        finally:
            unliteral(dict, "bar_dict")

        with self.assertRaises(AttributeError, msg="dict unhook failed"):
            {**a, **b}.bar_dict
    
    def test_implicit_string_concat_strict(self):
        @literal(str, strict=True)
        def bar_str(self):
            return "correct"
        
        try:
            self.assertEqual("1" "2" "3".bar_str, "correct", "implicit string concat hook failed")
        finally:
            unliteral(str, "bar_str")

        with self.assertRaises(AttributeError, msg="implicit string concat unhook failed"):
            "1" "2" "3".bar_str

if __name__ == '__main__':
    unittest.main()