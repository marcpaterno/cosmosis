#include "c_datablock.h"
#include <stdio.h>
#include <assert.h>

void test_sections()
{
  c_datablock* s;
  s = make_c_datablock();

  assert(c_datablock_has_section(NULL, NULL) == DBS_DATABLOCK_NULL);
  assert(c_datablock_has_section(s, NULL) == DBS_NAME_NULL);
  assert(c_datablock_num_sections(NULL) == -1);

  assert(c_datablock_has_section(s, "cow") == DBS_SECTION_NOT_FOUND);
  assert(c_datablock_num_sections(s) == 0);

  /* Creating a parameter in a section must create the section. */
  assert(c_datablock_put_int(s, "s1", "a", 10) == DBS_SUCCESS);
  assert(c_datablock_has_section(s, "s1") == DBS_SUCCESS);
  assert(c_datablock_num_sections(s) == 1);

  destroy_c_datablock(s);
}

void test_scalar_double()
{
  double val, expected;
  c_datablock* s;
  s = make_c_datablock();
  assert(s);

  expected = 3.5;

  /* Put with no previous value should save the right value. */
  assert(c_datablock_put_double(s, "x", "cow", expected) == 0);
  assert(c_datablock_get_double(s, "x", "cow", &val) == 0);
  assert(val == expected);

  /* Second put of the same name with same type should fail, and the
     value should be unaltered. */
  assert(c_datablock_put_double(s, "x", "cow", 10.5) == DBS_NAME_ALREADY_EXISTS);
  val = 0.0;
  assert(c_datablock_get_double(s, "x", "cow", &val) == 0);
  assert(val == expected);

  /* Second put of the same name with different type should fail, and
     the value should be unaltered. */
  assert(c_datablock_put_int(s, "x", "cow", 2112) == DBS_NAME_ALREADY_EXISTS);
  val = 0.0;
  assert(c_datablock_get_double(s, "x", "cow", &val) == 0);
  assert(val == expected);

  destroy_c_datablock(s);
}

void test_scalar_int()
{
  int val, expected;
  c_datablock* s;
  s = make_c_datablock();
  assert(s);

  expected = -4;

  /* Put with no previous value should save the right value. */
  assert(c_datablock_put_int(s, "x", "cow", expected) == 0);
  assert(c_datablock_get_int(s, "x", "cow", &val) == 0);
  assert(val == expected);

  /* Put of the same name into a different section should not collide. */
  assert(c_datablock_put_int(s, "y", "cow", expected) == 0);
  assert(c_datablock_get_int(s, "y", "cow", &val) == 0);
  assert(val == expected);

  /* Second put of the same name with same type should fail, and the
     value should be unaltered. */
  assert(c_datablock_put_int(s, "x", "cow", 100) == DBS_NAME_ALREADY_EXISTS);
  val = 0;
  assert(c_datablock_get_int(s, "x", "cow", &val) == 0);
  assert(val == expected);

  /* Second put of the same name with different type should fail, and
     the value should be unaltered. */
  assert(c_datablock_put_double(s, "x", "cow", 10.5) == DBS_NAME_ALREADY_EXISTS);
  val = 0;
  assert(c_datablock_get_int(s, "x", "cow", &val) == 0);
  assert(val == expected);

  destroy_c_datablock(s);
}


  /*
  double x[] = {1,2,3};
  c_datablock_put_double_array_1d(s, "pig", x, 3);
  */

  /*
  double* y;
  int sz;
  c_datablock_get_double_array_1d(s, "pig", &y, &sz);
  */

  /*
  double z[4];
  int szz;
  c_datablock_get_double_array_1d_preallocated(s, "pig", z, &szz, 4);
  assert(szz == 3);
  assert(z[0] == 1);
  assert(z[1] == 2);
  */


int main()
{
  test_sections();
  test_scalar_int();
  test_scalar_double();

  return 0;
}
