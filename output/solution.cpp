class UnionFind {
public:
    vector<int> parent;
    UnionFind(int n) {
        parent.resize(n);
        for (int i = 0; i < n; i++) {
            parent[i] = i;
        }
    }

    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }

    void unionNodes(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        if (rootX != rootY) {
            parent[rootX] = rootY;
        }
    }
};

class Solution {
public:
    vector<bool> areConnected(int n, vector<int>& nums, int threshold, vector<vector<int>>& queries) {
        UnionFind uf(n);
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (abs(nums[i] - nums[j]) <= threshold) {
                    uf.unionNodes(i, j);
                }
            }
        }
        
        vector<bool> result;
        for (auto& query : queries) {
            result.push_back(uf.find(query[0]) == uf.find(query[1]));
        }
        return result;
    }
};