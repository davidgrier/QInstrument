from qtpy import QtCore


class QPollingMixin:
    '''Mixin that adds self-scheduling poll loop to an instrument.

    Instruments that need to update their properties continuously
    (e.g. lock-in amplifiers, stage controllers) inherit from this
    mixin alongside their transport base class.

    The poll loop is self-scheduling: :meth:`_poll` does its work and
    then schedules its own next call via ``QTimer.singleShot``.  The
    delay between the end of one response and the start of the next
    query is :attr:`POLL_INTERVAL` milliseconds.  Setting
    ``POLL_INTERVAL = 0`` gives maximum throughput; the instrument
    never backs up because the next query only starts after the
    previous one completes.

    :meth:`startPolling` must be called from the thread that owns the
    instrument (the worker thread, after :meth:`moveToThread`).
    :meth:`QInstrumentWidget` and :meth:`QInstrumentTree` handle this
    automatically via ``QMetaObject.invokeMethod``.

    :meth:`stopPolling` may be called from any thread — it only sets
    a flag that :meth:`_poll` checks before scheduling its next call.

    Usage
    -----
    .. code-block:: python

        class QMyInstrument(QPollingMixin, QSerialInstrument):
            POLL_INTERVAL = 100   # ms

            def _poll(self) -> None:
                if not getattr(self, '_polling', False):
                    return
                # batched query
                x, y = self._snap()
                self.propertyValue.emit('x', x)
                self.propertyValue.emit('y', y)
                if getattr(self, '_polling', False):
                    QtCore.QTimer.singleShot(
                        self.POLL_INTERVAL, self._poll)
    '''

    POLL_INTERVAL: int = 0
    '''Milliseconds between the end of one poll response and the start
    of the next query.  Default: ``0`` (maximum throughput).'''

    @QtCore.Slot()
    def startPolling(self) -> None:
        '''Start the self-scheduling poll loop.

        Sets the polling flag and fires the first :meth:`_poll` call
        immediately.  Must be called from the instrument's own thread
        so that the ``QTimer.singleShot`` calls inside :meth:`_poll`
        are owned by the correct thread.
        '''
        self._polling = True
        self._poll()

    @QtCore.Slot()
    def stopPolling(self) -> None:
        '''Stop the poll loop.

        Sets the polling flag to ``False``.  The current :meth:`_poll`
        call (if any) completes normally; no further calls are
        scheduled.  Safe to call from any thread.
        '''
        self._polling = False

    def _poll(self) -> None:
        '''Poll the instrument once and schedule the next call.

        The default implementation calls :meth:`get` for every
        registered property, which emits :attr:`propertyValue` for
        each one.  Override this in instruments that can batch
        multiple properties into a single query for efficiency.

        Subclass implementations must follow the same guard pattern::

            if not getattr(self, '_polling', False):
                return
            # ... do work ...
            if getattr(self, '_polling', False):
                QtCore.QTimer.singleShot(
                    self.POLL_INTERVAL, self._poll)
        '''
        if not getattr(self, '_polling', False):
            return
        for name in self.properties:
            self.get(name)
        if getattr(self, '_polling', False):
            QtCore.QTimer.singleShot(self.POLL_INTERVAL, self._poll)


__all__ = ['QPollingMixin']
