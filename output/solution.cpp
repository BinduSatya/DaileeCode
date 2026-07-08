class Solution {
public:
    vector<int> sumAndMultiply(string s, vector<vector<int>>& queries) {
        vector<int> result;
        int mod = 1e9 + 7;
        
        for (auto& query : queries) {
            string x = "";
            int sum = 0;
            
            for (int i = query[0]; i <= query[1]; i++) {
                if (s[i] != '0') {
                    x += s[i];
                    sum += s[i] - '0';
                }
            }
            
            int answer = 0;
            if (x != "") {
                answer = stoi(x) % mod * sum % mod;
            }
            
            result.push_back(answer);
        }
        
        return result;
    }
};