class Solution {
public:
    int totalWaviness(int num1, int num2) {
        int total = 0;
        for (int i = num1; i <= num2; i++) {
            string str = to_string(i);
            if (str.length() < 3) continue;
            for (int j = 1; j < str.length() - 1; j++) {
                if (str[j - 1] < str[j] && str[j] > str[j + 1]) {
                    total++;
                } else if (str[j - 1] > str[j] && str[j] < str[j + 1]) {
                    total++;
                }
            }
        }
        return total;
    }
};