class Solution {
public:
    string mapWordWeights(vector<string>& words, vector<int>& weights) {
        string result;
        for (const auto& word : words) {
            int weight = 0;
            for (const auto& c : word) {
                weight += weights[c - 'a'];
            }
            char mappedChar = 'a' + (25 - (weight % 26));
            result.push_back(mappedChar);
        }
        return result;
    }
};