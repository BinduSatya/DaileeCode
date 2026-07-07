class Solution {
public:
    long long sumAndMultiply(int n) {
        string x = "";
        int sum = 0;

        while (n > 0) {
            int digit = n % 10;
            if (digit != 0) {
                x = to_string(digit) + x;
                sum += digit;
            }
            n /= 10;
        }

        return (x.empty() ? 0 : stol(x)) * (x.empty() ? 0 : sum);
    }
};