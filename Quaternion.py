
import math
import adsk.core

class Quaternion:
	def __init__(self, w, x, y, z):
		self.w = w
		self.x = x
		self.y = y
		self.z = z

	@staticmethod
	def from_axis_angle(axis, angle):
		half_angle = angle / 2
		sin_half_angle = math.sin(half_angle)
		return Quaternion(
			math.cos(half_angle),
			axis.x * sin_half_angle,
			axis.y * sin_half_angle,
			axis.z * sin_half_angle
		)

	def __mul__(self, other):
		return Quaternion(
			self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
			self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
			self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
			self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
		)

	def to_matrix3d(self):
		xx = self.x * self.x
		yy = self.y * self.y
		zz = self.z * self.z
		xy = self.x * self.y
		xz = self.x * self.z
		yz = self.y * self.z
		wx = self.w * self.x
		wy = self.w * self.y
		wz = self.w * self.z

		return [
			1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy), 0,
			2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx), 0,
			2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy), 0,
			0, 0, 0, 1
		]

	def transform_vector(self, vector):
		q_vector = Quaternion(0, vector.x, vector.y, vector.z)
		q_conjugate = Quaternion(self.w, -self.x, -self.y, -self.z)
		q_result = self * q_vector * q_conjugate
		return adsk.core.Vector3D.create(q_result.x, q_result.y, q_result.z)