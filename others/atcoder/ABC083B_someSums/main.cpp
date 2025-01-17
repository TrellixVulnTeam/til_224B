/// @file

#include <cmath>
#include <iostream>
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
  int n;
  int a;
  int b;
  is >> n >> a >> b;

  int totalSum(0);
  for (int i = 1; i <= n; ++i) {
    int sum(0);
    int rest(i);
    for (int j = 4; j >= 0; --j) {
      const int MOD = rest % 10;
      rest /= 10;
      sum += MOD;
    }
    if ((a <= sum) && (sum <= b)) totalSum += i;
  }

  os << totalSum << "\n";

  return true;
}
}  // unnamed namespace
