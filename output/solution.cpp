class Solution {
public:
    int maxBuilding(int n, vector<vector<int>>& restrictions) {
        restrictions.push_back({1, 0});
        sort(restrictions.begin(), restrictions.end());
        
        for (int i = 0; i < restrictions.size() - 1; i++) {
            restrictions[i][1] = min(restrictions[i][1], restrictions[i + 1][1] + restrictions[i + 1][0] - restrictions[i][0]);
        }
        
        for (int i = restrictions.size() - 1; i > 0; i--) {
            restrictions[i - 1][1] = min(restrictions[i - 1][1], restrictions[i][1] + restrictions[i][0] - restrictions[i - 1][0]);
        }
        
        int ans = 0;
        for (int i = 0; i < restrictions.size() - 1; i++) {
            ans = max(ans, restrictions[i][1] + (restrictions[i + 1][0] - restrictions[i][0] - 1) / 2);
        }
        
        return ans;
    }
};