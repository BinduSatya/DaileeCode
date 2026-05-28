class Solution {
public:
    vector<int> stringIndices(vector<string>& wordsContainer, vector<string>& wordsQuery) {
        vector<int> result;
        for (const auto& query : wordsQuery) {
            int maxLen = 0, minLen = INT_MAX, index = -1;
            for (int i = 0; i < wordsContainer.size(); i++) {
                int commonLen = 0;
                for (int j = query.size() - 1, k = wordsContainer[i].size() - 1; j >= 0 && k >= 0; j--, k--) {
                    if (query[j] != wordsContainer[i][k]) break;
                    commonLen++;
                }
                if (commonLen > maxLen) {
                    maxLen = commonLen;
                    minLen = wordsContainer[i].size();
                    index = i;
                } else if (commonLen == maxLen) {
                    if (wordsContainer[i].size() < minLen) {
                        minLen = wordsContainer[i].size();
                        index = i;
                    }
                }
            }
            result.push_back(index);
        }
        return result;
    }
};