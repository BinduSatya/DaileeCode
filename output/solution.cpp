class Solution {
public:
    long long totalWaviness(long long num1, long long num2) {
        long long total = 0;
        for (long long num = num1; num <= num2; num++) {
            string str = to_string(num);
            int n = str.size();
            if (n < 3) continue;
            int waviness = 0;
            for (int i = 1; i < n - 1; i++) {
                if (str[i - 1] < str[i] && str[i] > str[i + 1]) waviness++;
                if (str[i - 1] > str[i] && str[i] < str[i + 1]) waviness++;
            }
            total += waviness;
        }
        return total;
    }
};