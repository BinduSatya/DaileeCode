class Solution {
public:
    int minimumCost(vector<int>& cost) {
        int n = cost.size();
        sort(cost.begin(), cost.end());
        int totalCost = 0;
        for (int i = n - 1; i >= 0; i--) {
            if (i > 1) {
                totalCost += cost[i] + cost[i - 1];
                i--;
            } else {
                totalCost += cost[i];
            }
        }
        return totalCost;
    }
};