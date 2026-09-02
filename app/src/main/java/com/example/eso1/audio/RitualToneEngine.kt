package com.example.eso1.audio

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import kotlin.math.PI
import kotlin.math.sin

class RitualToneEngine {
    @Volatile
    private var running = false
    private var worker: Thread? = null
    private var audioTrack: AudioTrack? = null

    fun start(baseFrequency: Float, intensity: Float) {
        stop()
        running = true

        worker = Thread {
            val sampleRate = 44_100
            val minBuffer = AudioTrack.getMinBufferSize(
                sampleRate,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )
            val track = AudioTrack.Builder()
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build()
                )
                .setAudioFormat(
                    AudioFormat.Builder()
                        .setSampleRate(sampleRate)
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build()
                )
                .setBufferSizeInBytes(minBuffer * 2)
                .setTransferMode(AudioTrack.MODE_STREAM)
                .build()

            audioTrack = track
            val buffer = ShortArray(1024)
            var phase = 0.0
            var lowPhase = 0.0
            val frequency = baseFrequency.coerceIn(70f, 420f).toDouble()
            val volume = (0.04f + intensity.coerceIn(0f, 1f) * 0.16f).toDouble()

            track.play()
            while (running) {
                for (index in buffer.indices) {
                    val wobble = sin(lowPhase) * 9.0
                    val carrier = sin(phase)
                    val overtone = sin(phase * 2.01) * 0.22
                    val sample = (carrier + overtone) * volume * (0.72 + sin(lowPhase * 0.37) * 0.28)
                    buffer[index] = (sample * Short.MAX_VALUE).toInt().toShort()
                    phase += 2.0 * PI * (frequency + wobble) / sampleRate
                    lowPhase += 2.0 * PI * 0.9 / sampleRate
                    if (phase > PI * 2.0) phase -= PI * 2.0
                    if (lowPhase > PI * 2.0) lowPhase -= PI * 2.0
                }
                track.write(buffer, 0, buffer.size)
            }
            track.stop()
            track.release()
        }.apply {
            name = "RitualToneEngine"
            isDaemon = true
            start()
        }
    }

    fun stop() {
        running = false
        worker?.join(120)
        worker = null
        audioTrack = null
    }
}
