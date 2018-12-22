/// @file

#include <algorithm>
#include <iostream>
#include <vector>

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
  const std::string WINNER_YOU("first");
  const std::string WINNER_RUNRUN("second");

  long n;
  is >> n;

  std::vector<long> a(n);
  for (long i = 0; i < n; ++i) is >> a[i];

  const long MIN_VAL = *std::min_element(a.begin(), a.end());

  const std::string* WINNER = &WINNER_YOU;
  if (MIN_VAL % 2 == 0) WINNER = &WINNER_RUNRUN;

  os << *WINNER << "\n";

  return true;
}
}  // unnamed namespace
