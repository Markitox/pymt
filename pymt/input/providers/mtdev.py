'''
MTDev: Native support of Multitouch device on Linux, using libmtdev.

Mtdev project is a part of Ubuntu Maverick multitouch architecture.
You can read more on http://wiki.ubuntu.com/Multitouch

To configure MTDev, it's preferable to use probesysfs providers.
Check :py:class:`~pymt.input.providers.probesysfs` for more information.

Otherwise, you can put in your configuration ::

    [input]
    # devicename = hidinput,/dev/input/eventXX
    acert230h = mtdev,/dev/input/event2

.. note::
    You must have read access to the input event.

You have the possibility to use custom range for some X, Y and pressure value.
On some drivers, the range reported is invalid.
To fix that, you can add one of theses options on the argument line :

* min_position_x : X minimum
* max_position_x : X maximum
* min_position_y : Y minimum
* max_position_y : Y maximum
* min_pressure : pressure minimum
* max_pressure : pressure maximum
* min_touch_major : width shape minimum
* max_touch_major : width shape maximum
* min_touch_minor : width shape minimum
* max_touch_minor : height shape maximum
'''

__all__ = ('MTDTouchProvider', 'MTDTouch')

import os
from pymt.input.touch import Touch
from pymt.input.shape import TouchShapeRect

class MTDTouch(Touch):
    def depack(self, args):
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        if 'size_w' in args and 'size_h' in args:
            self.shape = TouchShapeRect()
            self.shape.width = args['size_w']
            self.shape.height = args['size_h']
            self.profile.append('shape')
        if 'pressure' in args:
            self.pressure = args['pressure']
            self.profile.append('pressure')
        super(MTDTouch, self).depack(args)

    def __str__(self):
        return '<MTDTouch id=%d pos=(%f, %f) device=%s>' % (self.id, self.sx, self.sy, self.device)

if 'PYMT_DOC' in os.environ:

    # documentation hack
    MTDTouchProvider = None

else:
    import threading
    import collections
    from pymt.lib.mtdev import Device, \
            MTDEV_TYPE_EV_ABS, MTDEV_CODE_SLOT, MTDEV_CODE_POSITION_X, \
            MTDEV_CODE_POSITION_Y, MTDEV_CODE_PRESSURE, \
            MTDEV_CODE_TOUCH_MAJOR, MTDEV_CODE_TOUCH_MINOR, \
            MTDEV_CODE_TRACKING_ID, MTDEV_ABS_POSITION_X, \
            MTDEV_ABS_POSITION_Y, MTDEV_ABS_TOUCH_MINOR, \
            MTDEV_ABS_TOUCH_MAJOR
    from pymt.input.provider import TouchProvider
    from pymt.input.factory import TouchFactory
    from pymt.logger import pymt_logger

    class MTDTouchProvider(TouchProvider):

        options = ('min_position_x', 'max_position_x',
                   'min_position_y', 'max_position_y',
                   'min_pressure', 'max_pressure',
                   'min_touch_major', 'max_touch_major',
                   'min_touch_minor', 'min_touch_major')

        def __init__(self, device, args):
            super(MTDTouchProvider, self).__init__(device, args)
            self._device = None
            self.input_fn = None
            self.default_ranges = dict()

            # split arguments
            args = args.split(',')
            if not args:
                pymt_logger.error('MTD: No filename pass to MTD configuration')
                pymt_logger.error('MTD: Use /dev/input/event0 for example')
                return None

            # read filename
            self.input_fn = args[0]
            pymt_logger.info('MTD: Read event from <%s>' % self.input_fn)

            # read parameters
            for arg in args[1:]:
                if arg == '':
                    continue
                arg = arg.split('=')

                # ensure it's a key = value
                if len(arg) != 2:
                    pymt_logger.error('MTD: invalid parameter %s, not in key=value format.' % arg)
                    continue

                # ensure the key exist
                key, value = arg
                if key not in MTDTouchProvider.options:
                    pymt_logger.error('MTD: unknown %s option' % key)
                    continue

                # ensure the value
                try:
                    self.default_ranges[key] = int(value)
                except ValueError:
                    pymt_logger.error('MTD: invalid value %s for option %s' % (key, value))
                    continue

                # all good!
                pymt_logger.info('MTD: Set custom %s to %d' % (key, int(value)))

        def start(self):
            if self.input_fn is None:
                return
            self.uid = 0
            self.queue = collections.deque()
            self.thread = threading.Thread(
                target=self._thread_run,
                kwargs=dict(
                    queue=self.queue,
                    input_fn=self.input_fn,
                    device=self.device,
                    default_ranges=self.default_ranges
                ))
            self.thread.daemon = True
            self.thread.start()

        def _thread_run(self, **kwargs):
            input_fn = kwargs.get('input_fn')
            queue = kwargs.get('queue')
            device = kwargs.get('device')
            drs = kwargs.get('default_ranges').get
            touches = {}
            touches_sent = []
            point = {}
            l_points = {}

            def process(points):
                for args in points:
                    tid = args['id']
                    try:
                        touch = touches[tid]
                    except KeyError:
                        touch = MTDTouch(device, tid, args)
                        touches[touch.id] = touch
                    touch.move(args)
                    action = 'move'
                    if tid not in touches_sent:
                        action = 'down'
                        touches_sent.append(tid)
                    if 'delete' in args:
                        action = 'up'
                        del args['delete']
                        touches_sent.remove(tid)
                    queue.append((action, touch))

            def normalize(value, vmin, vmax):
                return (value - vmin) / float(vmax - vmin)

            # open mtdev device
            _fn = self.input_fn
            _slot = 0
            _device = Device(_fn)
            _changes = set()

            # prepare some vars to get limit of some component
            ab = _device.get_abs(MTDEV_ABS_POSITION_X)
            range_min_position_x    = drs('min_position_x', ab.minimum)
            range_max_position_x    = drs('max_position_x', ab.maximum)
            pymt_logger.info('MTD: <%s> range position X is %d - %d' %
                             (_fn, range_min_position_x, range_max_position_x))

            ab = _device.get_abs(MTDEV_ABS_POSITION_Y)
            range_min_position_y    = drs('min_position_y', ab.minimum)
            range_max_position_y    = drs('max_position_y', ab.maximum)
            pymt_logger.info('MTD: <%s> range position Y is %d - %d' %
                             (_fn, range_min_position_y, range_max_position_y))

            ab = _device.get_abs(MTDEV_ABS_TOUCH_MAJOR)
            range_min_major         = drs('min_touch_major', ab.minimum)
            range_max_major         = drs('max_touch_major', ab.maximum)
            pymt_logger.info('MTD: <%s> range touch major is %d - %d' %
                             (_fn, range_min_major, range_max_major))

            ab = _device.get_abs(MTDEV_ABS_TOUCH_MINOR)
            range_min_minor         = drs('min_touch_minor', ab.minimum)
            range_max_minor         = drs('max_touch_minor', ab.maximum)
            pymt_logger.info('MTD: <%s> range touch minor is %d - %d' %
                             (_fn, range_min_minor, range_max_minor))

            range_min_pressure      = drs('min_pressure', 0)
            range_max_pressure      = drs('max_pressure', 255)
            pymt_logger.info('MTD: <%s> range pressure is %d - %d' %
                             (_fn, range_min_pressure, range_max_pressure))

            while _device:
                # idle as much as we can.
                while _device.idle(1000):
                    continue

                # got data, read all without redoing idle
                while True:
                    data = _device.get()
                    if data is None:
                        break

                    # set the working slot
                    if data.type == MTDEV_TYPE_EV_ABS and \
                       data.code == MTDEV_CODE_SLOT:
                        _slot = data.value
                        continue

                    # fill the slot
                    if not _slot in l_points:
                        l_points[_slot] = dict()
                    point = l_points[_slot]
                    ev_value = data.value
                    ev_code = data.code
                    if ev_code == MTDEV_CODE_POSITION_X:
                        point['x'] = normalize(ev_value,
                            range_min_position_x, range_max_position_x)
                    elif ev_code == MTDEV_CODE_POSITION_Y:
                        point['y'] = 1. - normalize(ev_value,
                            range_min_position_y, range_max_position_y)
                    elif ev_code == MTDEV_CODE_PRESSURE:
                        point['pressure'] = normalize(ev_value,
                            range_min_pressure, range_max_pressure)
                    elif ev_code == MTDEV_CODE_TOUCH_MAJOR:
                        point['size_w'] = normalize(ev_value,
                            range_min_major, range_max_major)
                    elif ev_code == MTDEV_CODE_TOUCH_MINOR:
                        point['size_h'] = normalize(ev_value,
                            range_min_minor, range_max_minor)
                    elif ev_code == MTDEV_CODE_TRACKING_ID:
                        if ev_value == -1:
                            point['delete'] = True
                        else:
                            point['id'] = ev_value
                    else:
                        # unrecognized command, ignore.
                        continue
                    _changes.add(_slot)

                # push all changes
                if _changes:
                    process([l_points[x] for x in _changes])
                    _changes.clear()

        def update(self, dispatch_fn):
            # dispatch all event from threads
            try:
                while True:
                    event_type, touch = self.queue.popleft()
                    dispatch_fn(event_type, touch)
            except:
                pass


    TouchFactory.register('mtdev', MTDTouchProvider)
