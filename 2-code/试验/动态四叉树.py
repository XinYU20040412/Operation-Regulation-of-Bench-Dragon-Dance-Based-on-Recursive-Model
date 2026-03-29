# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 11:11:14 2024

@author: ASUS
"""

class QuadtreeNode:
    def __init__(self, bounds, capacity):
        self.bounds = bounds
        self.capacity = capacity
        self.objects = []
        self.divided = False
        self.nw = self.ne = self.sw = self.se = None

    def subdivide(self):
        bx, by, bw, bh = self.bounds
        hw, hh = bw / 2, bh / 2
        self.nw = QuadtreeNode((bx, by, hw, hh), self.capacity)
        self.ne = QuadtreeNode((bx + hw, by, hw, hh), self.capacity)
        self.sw = QuadtreeNode((bx, by + hh, hw, hh), self.capacity)
        self.se = QuadtreeNode((bx + hw, by + hh, hw, hh), self.capacity)
        self.divided = True

    def insert(self, obj):
        if not self._contains(self.bounds, obj):
            return False
        if len(self.objects) < self.capacity:
            self.objects.append(obj)
            return True
        if not self.divided:
            self.subdivide()
        return (self.nw.insert(obj) or self.ne.insert(obj) or
                self.sw.insert(obj) or self.se.insert(obj))

    def _contains(self, bounds, obj):
        bx, by, bw, bh = bounds
        ox, oy, ow, oh = obj
        return not (ox + ow < bx or ox > bx + bw or oy + oh < by or oy > by + bh)

    def query(self, range, found):
        if not self._intersects(self.bounds, range):
            return
        for obj in self.objects:
            if self._intersects(obj, range):
                found.append(obj)
        if self.divided:
            self.nw.query(range, found)
            self.ne.query(range, found)
            self.sw.query(range, found)
            self.se.query(range, found)

    def _intersects(self, bounds1, bounds2):
        x1, y1, w1, h1 = bounds1
        x2, y2, w2, h2 = bounds2
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

# 示例用法
quadtree = QuadtreeNode((0, 0, 100, 100), 4)
rect1 = (10, 10, 20, 20)
rect2 = (50, 50, 30, 30)
quadtree.insert(rect1)
quadtree.insert(rect2)

found = []
quadtree.query((0, 0, 60, 60), found)
print("Found objects:", found)
