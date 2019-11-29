/// @file

#include <iostream>
#include <set>
#include <string>

namespace {

bool run(std::istream& is, std::ostream& os);
}  // unnamed namespace

/// @brief エントリポイント
#ifdef _TEST
static int run()
#else
int main()
#endif
{
  try {
    if (run(std::cin, std::cout) == false) {
      std::cerr << "main funciton error.\n";
      return EXIT_FAILURE;
    }
  } catch (const std::exception& e) {
    std::cerr << "catch exception\n";
    std::cerr << e.what() << "\n";
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

namespace {

/// @brief 実行処理
bool run(std::istream& is, std::ostream& os)
{
  // 鏡餅の一枚ずつの半径を取得
  int n;
  is >> n;

  std::set<int> radiusSet;
  for (int i = 0; i < n; ++i) {
    int r;
    is >> r;
    radiusSet.insert(r);
  }

  os << radiusSet.size() << "\n";

  return true;
}
}  // unnamed namespace
