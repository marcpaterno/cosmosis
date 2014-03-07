#ifndef COSMOSIS_SECTION_HH
#define COSMOSIS_SECTION_HH

#include <initializer_list>
#include <map>
#include <string>

#include "exceptions.hh"
#include "entry.hh"
#include "datablock_status.h"

namespace cosmosis
{
  // A Section represents a related set of named quantities, and
  // provides 'get', 'put', and 'replace' ability for each type of
  // quantity.
  //
  // Original author: Marc Paterno (paterno@fnal.gov)

  class Section
  {
  public:
    struct BadSectionAccess : cosmosis::Exception { }; // used for exceptions

    template <class T>
    DATABLOCK_STATUS put_val(std::string const& name, T const& value);

    template <class T>
    DATABLOCK_STATUS replace_val(std::string const& name, T const& value);

    // return true if we have a value of the right type for the given name.
    template <class T> bool has_value(std::string const& name) const;

    template <class T> 
    DATABLOCK_STATUS get_val(std::string const& name, T& v) const;

    // Return true if we have a value of any type with the given name.
    bool has_val(std::string const& name) const;

    // The view functions provide readonly access to the data in the
    // Section without copying the data. The reference returned by a
    // call to view is invalidated if any replace function is called for
    // the same name. Throws BadSectionAccess if the name can't be
    // found, and BadEntry if the contained value is the wrong type.
    template <class T>
    T const& view(std::string const& name) const;

  private:
    std::map<std::string, Entry> vals_;
  };
}

template <class T>
DATABLOCK_STATUS 
cosmosis::Section::put_val(std::string const& name, T const& v)
{
  auto i = vals_.find(name);
  if (i == vals_.end() )
    {
      vals_.emplace(name, Entry(v));
      return DBS_SUCCESS;
    }
  return DBS_NAME_ALREADY_EXISTS;
}

template <class T>
DATABLOCK_STATUS
cosmosis::Section::replace_val(std::string const& name, T const& v)
{
  auto i = vals_.find(name);
  if (i == vals_.end()) return DBS_NAME_NOT_FOUND;
  if (not i->second.is<T>()) return DBS_WRONG_VALUE_TYPE;
  i->second.set_val(v);
  return DBS_SUCCESS;
}

template <class T>
bool 
cosmosis::Section::has_value(std::string const& name) const
{
  auto i = vals_.find(name);
  return (i != vals_.end()) && i->second.is<T>();
}

template <class T>
DATABLOCK_STATUS
cosmosis::Section::get_val(std::string const& name, T& v) const
{
  auto i = vals_.find(name);
  if (i == vals_.end()) return DBS_NAME_NOT_FOUND;
  if (not i->second.is<T>()) return DBS_WRONG_VALUE_TYPE;
  v = i->second.val<T>();
  return DBS_SUCCESS;  
}

template <class T>
T const& 
cosmosis::Section::view(std::string const& name) const
{
  auto i = vals_.find(name);
  if (i == vals_.end()) throw BadSectionAccess();
  return i->second.view<T>();
}

#endif
