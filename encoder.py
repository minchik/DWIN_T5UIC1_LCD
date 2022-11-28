# Class to monitor a rotary encoder and update a value.  You can either read the value when you need it,
# by calling get_value(), or you can configure a callback which will be called whenever the value changes.

from RPi import GPIO


class Encoder:
    def __init__(self, left_pin, right_pin, callback=None):
        self.leftPin = left_pin
        self.rightPin = right_pin
        self.value = 0
        self.state = '00'
        self.direction = None
        self.callback = callback
        GPIO.setup(self.leftPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.rightPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.leftPin, GPIO.BOTH, callback=self.transition_occurred)
        GPIO.add_event_detect(self.rightPin, GPIO.BOTH, callback=self.transition_occurred)

    def transition_occurred(self, channel):
        p1 = GPIO.input(self.leftPin)
        p2 = GPIO.input(self.rightPin)
        new_state = "{}{}".format(p1, p2)

        if self.state == "00":  # Resting position
            if new_state == "01":  # Turned right 1
                self.direction = "R"
            elif new_state == "10":  # Turned left 1
                self.direction = "L"

        elif self.state == "01":  # R1 or L3 position
            if new_state == "11":  # Turned right 1
                self.direction = "R"
            elif new_state == "00":  # Turned left 1
                if self.direction == "L":
                    self.value = self.value - 1
                    if self.callback is not None:
                        self.callback(self.value)

        elif self.state == "10":  # R3 or L1
            if new_state == "11":  # Turned left 1
                self.direction = "L"
            elif new_state == "00":  # Turned right 1
                if self.direction == "R":
                    self.value = self.value + 1
                    if self.callback is not None:
                        self.callback(self.value)

        else:  # self.state == "11"
            if new_state == "01":  # Turned left 1
                self.direction = "L"
            elif new_state == "10":  # Turned right 1
                self.direction = "R"
            # Skipped an intermediate 01 or 10 state, but if we know direction then a turn is complete
            elif new_state == "00":
                if self.direction == "L":
                    self.value = self.value - 1
                    if self.callback is not None:
                        self.callback(self.value)
                elif self.direction == "R":
                    self.value = self.value + 1
                    if self.callback is not None:
                        self.callback(self.value)
                
        self.state = new_state

    def get_value(self):
        return self.value
