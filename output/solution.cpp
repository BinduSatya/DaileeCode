class Solution {
public:
    vector<int> arrayRankTransform(vector<int>& arr) {
        vector<int> sorted = arr;
        sort(sorted.begin(), sorted.end());
        map<int, int> ranks;
        int rank = 1;
        
        for (int num : sorted) {
            if (ranks.find(num) == ranks.end()) {
                ranks[num] = rank++;
            }
        }
        
        vector<int> result;
        for (int num : arr) {
            result.push_back(ranks[num]);
        }
        
        return result;
    }
};