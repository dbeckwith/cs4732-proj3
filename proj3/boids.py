# -*- coding: utf-8 -*-

import math
import random
import itertools

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPolygonF, QPen, QBrush

from . import util


class BoidSim(object):
    """
    Class representing a simulation of boids.
    """

    # what team each team is attracted to
    team_attractions = {
        'red': 'blue',
        'blue': 'green',
        'green': 'red'
    }
    # what team each team is trying to evade
    team_evasions = {
        'red': 'green',
        'blue': 'red',
        'green': 'blue'
    }

    def __init__(self, scene, bounds_radius):
        """
        Creates a new BoidSim.

        Arguments:
            scene: QGraphicsScene, the scene to place the graphics objects of the simulation in
            bounds_radius: float, the radius of the simulation boundary in pixels
        """
        self.scene = scene
        self.bounds_radius = bounds_radius

        # create boids
        self.boids = set()
        for team in Boid.team_colors.keys():
            # 30 for each team
            for _ in range(30):
                # pick random position and velocity in polar coordinates
                pr = random.uniform(0, bounds_radius)
                pt = random.uniform(0, math.pi * 2)
                vr = Boid.speed
                vt = random.uniform(0, math.pi * 2)
                self.boids.add(Boid(self,
                    team,
                    QPointF(pr * math.cos(pt), pr * math.sin(pt)),
                    QPointF(vr * math.cos(vt), vr * math.sin(vt))))

        # create obstacles
        self.obstacles = set()
        for _ in range(6):
            # pick random position in polar coordinates
            pr = random.uniform(0, bounds_radius)
            pt = random.uniform(0, math.pi * 2)
            # pick random radius
            r = random.uniform(20, 50)
            self.obstacles.add(Obstacle(self,
                    QPointF(pr * math.cos(pt), pr * math.sin(pt)),
                    r))

        # create circle showing boundary
        self.bounds = self.scene.addEllipse(
            -bounds_radius, -bounds_radius,
            bounds_radius * 2, bounds_radius * 2,
            QPen(),
            QBrush())

    def update(self, dt):
        """
        Updates one frame of the simulation.

        Arguments:
            dt: float, the timestep in seconds
        """

        # first calculate acceleration for each boid
        for boid in self.boids:
            # start at no acceleration
            boid.acceleration = QPointF()

            # repelling force from boundary
            # ramps from 0 at visual range to a lot at the boundary's edge
            # always pointed towards center
            bounds_repel = util.lerp(util.length(boid.position), self.bounds_radius - Boid.visual_range, self.bounds_radius, 0, 2000, True) * util.normalized_or_null(-boid.position)
            boid.acceleration += bounds_repel

            # repelling forces for each obstacle
            for obstacle in self.obstacles:
                # vector pointing torwards boid from obstacle
                dpos = boid.position - obstacle.position
                # ramps from 0 at visual range to a lot at the obstacle's edge
                # pointed away from obstacle towards boid
                obstacle_repel = util.lerp(util.length(dpos), obstacle.radius + Boid.visual_range, obstacle.radius, 0, 2000, True) * util.normalized_or_null(dpos)
                boid.acceleration += obstacle_repel

            # collect all boids in this boid's neighborhood that:
            #   aren't this boid
            #   are on this boid's team
            #   are within sight of this boid
            boid.neighborhood = set(neighbor for neighbor in self.boids if \
                neighbor != boid and \
                neighbor.team == boid.team and \
                util.lengthsq(neighbor.position - boid.position) < boid.visual_range ** 2)
            # if there were any in the neighborhood
            if boid.neighborhood:
                # separation force
                # add up vectors from neighbors towards this boid
                # but only for neighbors on this team or on this boid's evasion team
                separation = sum((boid.position - neighbor.position for neighbor in boid.neighborhood if \
                    boid.team == neighbor.team or \
                    self.team_evasions[boid.team] == neighbor.team), QPointF())
                boid.acceleration += separation / 30 * 60

                # alignment force
                # first get average heading of neighbors by summing velocities and dividing by number of neighbors
                avg_heading = sum((neighbor.velocity for neighbor in boid.neighborhood), QPointF()) / len(boid.neighborhood)
                # then add a force pointing from this boid's velocity towards the average heading
                alignment = avg_heading - boid.velocity
                boid.acceleration += alignment / 8 * 60

                # cohesion force
                # first get average position of neighbors by summing positions and dividing by number of neighbors
                # but only for neighbors on this team or on this boid's attraction team
                avg_position = sum((neighbor.position for neighbor in boid.neighborhood if \
                    boid.team == neighbor.team or \
                    self.team_attractions[boid.team] == neighbor.team), QPointF()) / len(boid.neighborhood)
                # then add a force pointing from this boid's position towards the average position
                cohesion = avg_position - boid.position
                boid.acceleration += cohesion / 100 * 60

        # update each boid's position and graphics
        for boid in self.boids:
            boid.update(dt)

        # handle team-conversion collisions
        # iterate through all combinations of boids without repetition
        for (boid1, boid2) in itertools.combinations(self.boids, 2):
            # vector pointing from boid1 to boid2
            dpos = boid2.position - boid1.position
            # if boids are colliding
            if util.lengthsq(boid2.position - boid1.position) < (boid1.collision_radius + boid2.collision_radius) ** 2:
                # flags indicating if each boid is facing the other
                boid1_facing = QPointF.dotProduct(dpos, boid1.velocity) > 0
                boid2_facing = QPointF.dotProduct(dpos, boid2.velocity) < 0

                # if one is facing the other and the other is facing away, the one facing away is the "prey"
                if boid1_facing and not boid2_facing:
                    predator = boid1
                    prey = boid2
                elif boid2_facing and not boid1_facing:
                    predator = boid2
                    prey = boid1
                # otherwise, choose prey randomly
                else:
                    predator, prey = random.sample([boid1, boid2], 2)

                # convert prey to predator's team
                prey.team = predator.team


class Boid(object):
    """
    Class representing a single boid.
    """

    speed = 100 # how fast the boid travels in pixels per second
    visual_range = 50 # how far the boid can see in pixels
    collision_radius = 10 # how big the boid is in pixels
    # hue values for teams
    team_colors = {
        'red': 0,
        'green': 120,
        'blue': 240
    }

    def __init__(self, sim, team, position, velocity):
        """
        Creates a new boid.

        Arguments:
            sim: BoidSim, the simulation this boid is part of
            team: str, the team this boid is on
            position: QPointF, the starting position of this boid
            velocity: QPointF, the starting velocity of this boid
        """
        self.sim = sim
        self.team = team
        self.position = position
        self.velocity = velocity

        # polygon for boid body
        self.body_graphic = sim.scene.addPolygon(
            QPolygonF([
                QPointF(1, 0),
                QPointF(-0.6, 0.6),
                QPointF(-0.3, 0),
                QPointF(-0.6, -0.6)]),
            QPen(Qt.NoPen),
            QBrush())
        self.body_graphic.setScale(self.collision_radius)

        # circle showing boid's range of vision
        self.visual_range_graphic = sim.scene.addEllipse(
            -self.visual_range, -self.visual_range,
            self.visual_range * 2, self.visual_range * 2,
            QPen(util.hsl(0, 0, 0, 20)),
            QBrush())
        self.visual_range_graphic.setVisible(False) # set to True to enable

        # group all graphics together so they can be transformed together
        self.graphics_group = sim.scene.createItemGroup([
            self.body_graphic,
            self.visual_range_graphic])

        # make sure graphics up-to-date
        self._update_graphics()

    def _update_graphics(self):
        """
        Updates the position and any other properties of the boid's graphics.
        """
        # update position
        self.graphics_group.setX(self.position.x())
        self.graphics_group.setY(self.position.y())
        # update body rotation towards velocity
        self.body_graphic.setRotation(util.rad2deg(math.atan2(self.velocity.y(), self.velocity.x())))
        # update body color by team
        self.body_graphic.setBrush(QBrush(util.hsl(self.team_colors[self.team], 90, 80)))

    def update(self, dt):
        """
        Updates the velocity, position, and graphics of the boid.
        """
        # update velocity
        self.velocity += self.acceleration * dt
        # set velocity magnitude to speed
        self.velocity = util.normalized(self.velocity) * self.speed

        # update position
        self.position += self.velocity * dt
        # if position out of bounds
        if util.lengthsq(self.position) > self.sim.bounds_radius ** 2:
            # move position in bounds and reflect velocity
            self.position /= util.length(self.position)
            self.velocity = self.velocity - 2 * QPointF.dotProduct(self.velocity, self.position) * self.position
            self.position *= self.sim.bounds_radius

        self._update_graphics()

class Obstacle(object):
    """
    Class representing a circular obstacle that boids avoid.
    """

    def __init__(self, sim, position, radius):
        """
        Creates a new obstacle.

        Arguments:
            sim: BoidSim, the simulation that this obstacle is part of
            position: QPointF, the position of this obstacle
            radius: float, the radius in pixels of this obstacle
        """
        self.sim = sim
        self.position = position
        self.radius = radius

        # create a circle graphic with the given radius
        self.graphic = sim.scene.addEllipse(
            -radius, -radius,
            radius * 2, radius * 2,
            QPen(Qt.NoPen),
            QBrush(util.hsl(0, 0, 10)))
        # move graphic
        self.graphic.setX(self.position.x())
        self.graphic.setY(self.position.y())
