class Solution {
public:
    vector<int> pivotArray(vector<int>& nums, int pivot) {
        vector<int> less, equal, greater;
        for (int num : nums) {
            if (num < pivot) less.push_back(num);
            else if (num == pivot) equal.push_back(num);
            else greater.push_back(num);
        }
        less.insert(less.end(), equal.begin(), equal.end());
        less.insert(less.end(), greater.begin(), greater.end());
        return less;
    }
};