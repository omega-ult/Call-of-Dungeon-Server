# -*- coding: utf-8 -*-
#======================================================================
#
# CoDTaskManager.py - manage tasks and schedule their execution 
#
# use TaskManager.addDelayTask to add a task that will be executed after 'delay' seconds
# use TaskManager.addSustainTask to add a task that will be executed ever 'delay' seconds
# use TaskManager.cancel to cancel an execution of specified task.
#
#======================================================================

import sys
import time
import heapq
import select

class DelayTask(object):
	"""
	Execute a function at a later time.
	"""
	def __init__(self, seconds, target, *args, **kwargs):
		super(DelayTask, self).__init__()
		self._delay = seconds
		self._target = target
		self._args = args
		self._kwargs = kwargs

		self.isCancelled = False
		self.timeOut = self._delay

	def __le__(self, other):
		return self.timeOut <= other.timeOut

	def execute(self):
		try:
			self._target(*self._args, **self._kwargs)
		except (KeyboardInterrupt, SystemExit):
			raise
		return False;

	def cancel(self):
		self.isCancelled = True

class SustainTask(DelayTask):
	"""
	Execute a function every x seconds.
	"""
	def execute(self):
		try:
			self._target(*self._args, **self._kwargs)
		except(KeyboardInterrupt, SystemExit):
			raise
		self.timeOut = time.time() + self._delay
		return True;


class TaskManager(object):
	tasks = []
	cancelledNum = 0

	@staticmethod
	def addDelayTask(delay, func, *args, **kwargs):
		_task = DelayTask(delay, func, *args, **kwargs)
		heapq.headpush(Taskmanager.tasks, _task)
		return task

	@staticmethod
	def addSustainTask(delay, func, *args, **kwargs):
		_task = SustainTask(delay, func, *args, **kwargs)
		heapq.heappush(TaskManager.tasks, _task)
		return _task

	@staticmethod
	def scheduler():
		_timeNow = time.time()

		while TaskManager.tasks and _timeNow >= TaskManager.tasks[0].timeOut:
			_task = heapq.heappop(TaskManager.tasks)
			if _task.isCancelled:
				TaskManager.cancelledNum  -= 1
				continue

			try:
				_shouldRepeat = _task.execute()
			except (KeyboardInterrupt, SystemExit):
				raise

			if _shouldRepeat:
				heapq.heappush(TaskManager.tasks, _task);

	@staticmethod
	def cancel(task):
		if not task in TaskManager.tasks:
			return

		task.cancel()
		TaskManager.cancelledNum += 1

		print "task cancelled"
		if float(TaskManager.cancelledNum)/len(TaskManager.tasks) > 0.25:
			TaskManager.removeCancelledTasks()
		return

	@staticmethod
	def removeCancelledTasks():
		print "remove cancelled tasks"
		_tmpTask = []
		for t in TaskManager.tasks:
			if not t.isCancelled:
				_tmpTask.append(t)

		TaskManager.tasks = _tmpTask
		heapq.heapify(TaskManager.tasks)

		TaskManager.cancelledNum = 0
		return


