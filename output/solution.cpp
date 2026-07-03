class Solution {
public:
    int findMaxPathScore(vector<vector<int>>& edges, vector<bool>& online, long long k) {
        int n = online.size();
        vector<vector<pair<int, int>>> g(n);
        for (auto& edge : edges) {
            if (online[edge[0]] && online[edge[1]]) {
                g[edge[0]].emplace_back(edge[1], edge[2]);
            }
        }
        
        vector<long long> dis(n, LLONG_MAX);
        dis[n - 1] = 0;
        priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
        pq.emplace(0, n - 1);
        
        while (!pq.empty()) {
            auto [d, v] = pq.top();
            pq.pop();
            if (d > dis[v]) continue;
            for (auto& [u, w] : g[v]) {
                if (dis[u] > dis[v] + w) {
                    dis[u] = dis[v] + w;
                    pq.emplace(dis[u], u);
                }
            }
        }
        
        if (dis[0] > k) return -1;
        
        int l = 0, r = 1e9 + 7;
        while (l < r) {
            int m = l + r + 1 >> 1;
            vector<long long> d(n, LLONG_MAX);
            d[n - 1] = 0;
            priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> q;
            q.emplace(0, n - 1);
            
            while (!q.empty()) {
                auto [cur, v] = q.top();
                q.pop();
                if (cur > d[v]) continue;
                for (auto& [u, w] : g[v]) {
                    if (d[u] > d[v] + w && w >= m) {
                        d[u] = d[v] + w;
                        q.emplace(d[u], u);
                    }
                }
            }
            
            if (d[0] <= k) l = m;
            else r = m - 1;
        }
        
        return l;
    }
};