class Solution {
public:
    int earliestFinishTime(vector<int>& landStartTime, vector<int>& landDuration, vector<int>& waterStartTime, vector<int>& waterDuration) {
        int minTime = INT_MAX;
        
        for (int i = 0; i < landStartTime.size(); i++) {
            for (int j = 0; j < waterStartTime.size(); j++) {
                minTime = min(minTime, max(landStartTime[i] + landDuration[i], waterStartTime[j]) + waterDuration[j]);
                minTime = min(minTime, max(waterStartTime[j] + waterDuration[j], landStartTime[i]) + landDuration[i]);
            }
        }
        
        return minTime;
    }
};