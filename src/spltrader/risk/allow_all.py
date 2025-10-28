class AllowAllRisk:
    def pre_place(self, req): return True
    def on_fill(self, f): pass