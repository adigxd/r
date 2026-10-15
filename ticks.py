# physics runs at a fixed rate (ticks per second) no matter how fast the frames are drawn
# every frame says how much time passed, and gets back how many physics ticks to run; what is left over (less than one tick) is kept for the next frame
# alpha says how far between the last two ticks the frame is, so the drawing can blend between them and motion stays smooth when frames and ticks don't line up

class Ticker:
    def __init__(self, tick_rate, max_frame_time=0.25):
        self.dt = 1.0 / tick_rate # length of one tick in seconds
        self.max_frame_time = max_frame_time # after a long freeze (dragging the window, ...) don't try to catch up on all of it
        self.leftover = 0.0

    def advance(self, frame_time):
        # returns how many ticks to run for a frame that took frame_time seconds
        self.leftover += min(frame_time, self.max_frame_time)
        ticks = 0

        while self.leftover >= self.dt:
            self.leftover -= self.dt
            ticks += 1

        return ticks

    @property
    def alpha(self):
        # 0 = the frame is exactly at the last tick, just under 1 = almost at the next one
        return self.leftover / self.dt
