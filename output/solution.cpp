class Solution {
public:
    int numberOfSubstrings(string s) {
        int n = s.size();
        int res = 0;
        for (int i = 0; i < n; i++) {
            int a = 0, b = 0, c = 0;
            for (int j = i; j < n; j++) {
                if (s[j] == 'a') a++;
                else if (s[j] == 'b') b++;
                else c++;
                if (a > 0 && b > 0 && c > 0) res++;
            }
        }
        return res;
    }
};