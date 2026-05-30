class Solution {
public:
    vector<bool> getResults(vector<vector<int>>& queries) {
        vector<bool> results;
        set<int> obstacles;
        for (auto& query : queries) {
            if (query[0] == 1) {
                obstacles.insert(query[1]);
            } else {
                bool canPlace = true;
                int x = query[1], sz = query[2];
                auto it = obstacles.lower_bound(0);
                int prev = 0;
                while (it != obstacles.end() && *it <= x) {
                    if (*it - prev < sz) {
                        canPlace = false;
                        break;
                    }
                    prev = *it;
                    ++it;
                }
                if (canPlace && prev + sz <= x) {
                    canPlace = true;
                } else {
                    canPlace = false;
                }
                results.push_back(canPlace);
            }
        }
        return results;
    }
};