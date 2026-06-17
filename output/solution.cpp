class Solution {
public:
    char processStr(string s, long long k) {
        string result = "";
        
        for (char c : s) {
            if (c == '*') {
                if (!result.empty()) result.pop_back();
            } else if (c == '#') {
                result += result;
            } else if (c == '%') {
                reverse(result.begin(), result.end());
            } else {
                result += c;
            }
        }
        
        if (k >= result.size()) return '.';
        return result[k];
    }
};