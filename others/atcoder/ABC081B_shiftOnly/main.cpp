/// @file

#include <cmath>
#include <iostream>
#include <limits>
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
  int arrayNum;
  is >> arrayNum;

  int minOperation(std::numeric_limits<int>::max());
  for (int i = 0; i < arrayNum; ++i) {
    int num;
    is >> num;

    int op(0);
    for (int i = 0; (num % 2 == 0) && (i < minOperation); ++op, ++i) num /= 2;
    if (op < minOperation) minOperation = op;
  }

  os << minOperation << "\n";

  return true;
}
}  // unnamed namespace
