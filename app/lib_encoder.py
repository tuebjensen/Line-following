


GPIO.add_event_detect(self._encoder_interrupt_pin, GPIO.FALLING, callback=self._encoder_callback)
GPIO.setup(self._encoder_interrupt_pin, GPIO.IN)
