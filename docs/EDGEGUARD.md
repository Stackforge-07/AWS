# EdgeGuard

## Implemented artifacts

- `edge/firmware/edgeguard.hpp`: portable C++ sample screening, elapsed-time ROC, EWMA residual, frozen-variable checks, timestamp checks and an acknowledged FIFO ring buffer with explicit overflow counts.
- `edge/tests/test_edge.cpp`: host-compiled tests for screening, timestamps, freezing, FIFO replay and overflow accounting.
- `ml/train_edge.py`: reproducible dense autoencoder training, full INT8 conversion, representative dataset, validation-derived threshold, C array generation and host timing.
- `edge/models/edgeguard_int8.tflite`, `model_data.h`, `metadata.json`, `autoencoder.keras`: actual generated artifacts.
- `edge/firmware/edgeguard_tflm.hpp`: integration adapter for a TensorFlow Lite Micro SDK, caller-provided tensor arena, quantization and reconstruction error.

The generated TFLite binary is 8,336 bytes. Host timings and threshold are stored in `metadata.json`; do not present them as ESP32/STM32 measurements. MCU latency, tensor arena, peak RAM, flash total and power remain null. The TFLM adapter has not been compiled with a board toolchain or flashed.

## Reproduce

```sh
make train
make train-edge
make benchmark-edge
make test-edge
```

`train-edge` uses isolated TensorFlow 2.20 and NumPy <2.3 dependencies. It does not enlarge the ordinary backend runtime. TensorFlow's desktop interpreter was used to verify INT8 input/output and measure host execution. [TensorFlow integer-quantization guidance](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/g3doc/performance/post_training_quantization.md) describes the representative-dataset and INT8 conversion path.

## Offline demonstration

The scenario lab's edge mode is a **software rules emulator**. Disconnecting stores target packets in a bounded SQLite buffer while other simulated stations continue. Reconnection replays packets with original timestamps through the central pipeline. Replays use the same stable observation IDs and preserve raw telemetry. It does not pretend to run the INT8 model on an attached MCU.

## Board integration still required

Select ESP32-S3 or STM32 and a pinned TFLM SDK. Supply sensor drivers, timer, persistent flash buffer, secure MQTT/HTTP transport, credentials and acknowledgement handling. Assemble the 36-value oldest-first window, use the exported training normalization and validation threshold, invoke TFLM and transmit the three-state edge output. Measure actual arena allocation, memory high-water mark, inference timing and firmware flash size on that board. Never use the desktop benchmark as a substitute. See [TFLM memory management](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/docs/memory_management.md).
