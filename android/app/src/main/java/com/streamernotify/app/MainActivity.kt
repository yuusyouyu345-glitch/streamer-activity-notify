package com.streamernotify.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AppRoot() }
    }
}

data class StreamerItem(val id: Long, val displayName: String)
data class PrefItem(val streamerId: Long, val platform: String, val eventType: String, val enabled: Boolean)
data class EventItem(
    val source: String,
    val eventType: String,
    val streamerId: Long,
    val occurredAt: String,
    val payload: String,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppRoot() {
    val apiBase = BuildConfig.API_BASE_URL
    val client = remember { OkHttpClient() }

    val streamers = remember { mutableStateListOf<StreamerItem>() }
    val prefs = remember { mutableStateListOf<PrefItem>() }
    val events = remember { mutableStateListOf<EventItem>() }

    var userIdInput by remember { mutableStateOf("1") }
    var statusText by remember { mutableStateOf("ready") }

    var prefStreamerId by remember { mutableStateOf("") }
    var prefPlatform by remember { mutableStateOf("youtube") }
    var prefEventType by remember { mutableStateOf("video_published") }
    var prefEnabled by remember { mutableStateOf(true) }

    var eventSourceFilter by remember { mutableStateOf("") }
    var eventLimit by remember { mutableStateOf("20") }

    fun loadStreamers() {
        Thread {
            runCatching {
                val req = Request.Builder().url("$apiBase/streamers").build()
                val body = client.newCall(req).execute().body?.string().orEmpty()
                val arr = JSONArray(body)
                buildList {
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        add(StreamerItem(o.getLong("id"), o.getString("display_name")))
                    }
                }
            }.onSuccess { items ->
                streamers.clear(); streamers.addAll(items)
                if (prefStreamerId.isBlank() && items.isNotEmpty()) prefStreamerId = items.first().id.toString()
                statusText = "loaded streamers=${items.size}"
            }.onFailure { statusText = "streamers error: ${it.message}" }
        }.start()
    }

    fun loadPrefs() {
        val userId = userIdInput.ifBlank { "1" }
        Thread {
            runCatching {
                val req = Request.Builder().url("$apiBase/notification-preferences?user_id=$userId").build()
                val body = client.newCall(req).execute().body?.string().orEmpty()
                val arr = JSONArray(body)
                buildList {
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        add(PrefItem(o.getLong("streamer_id"), o.getString("platform"), o.getString("event_type"), o.getBoolean("enabled")))
                    }
                }
            }.onSuccess { items ->
                prefs.clear(); prefs.addAll(items)
                statusText = "loaded prefs=${items.size}"
            }.onFailure { statusText = "prefs error: ${it.message}" }
        }.start()
    }

    fun loadEvents() {
        Thread {
            runCatching {
                val src = eventSourceFilter.trim()
                val lim = eventLimit.toIntOrNull()?.coerceIn(1, 200) ?: 20
                val url = buildString {
                    append("$apiBase/events?limit=$lim")
                    if (src.isNotBlank()) append("&source=$src")
                }
                val req = Request.Builder().url(url).build()
                val body = client.newCall(req).execute().body?.string().orEmpty()
                val arr = JSONArray(body)
                buildList {
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        add(
                            EventItem(
                                source = o.getString("source"),
                                eventType = o.getString("event_type"),
                                streamerId = o.getLong("streamer_id"),
                                occurredAt = o.getString("occurred_at"),
                                payload = o.optString("payload_json", ""),
                            )
                        )
                    }
                }
            }.onSuccess { items ->
                events.clear(); events.addAll(items)
                statusText = "loaded events=${items.size}"
            }.onFailure { statusText = "events error: ${it.message}" }
        }.start()
    }

    fun savePref() {
        val userId = userIdInput.toLongOrNull() ?: 1L
        val streamerId = prefStreamerId.toLongOrNull() ?: return
        Thread {
            runCatching {
                val payload = JSONObject().apply {
                    put("user_id", userId)
                    put("streamer_id", streamerId)
                    put("platform", prefPlatform)
                    put("event_type", prefEventType)
                    put("enabled", prefEnabled)
                }
                val req = Request.Builder()
                    .url("$apiBase/notification-preferences")
                    .post(payload.toString().toRequestBody("application/json".toMediaType()))
                    .build()
                client.newCall(req).execute().use { res -> if (!res.isSuccessful) error("save failed: ${res.code}") }
            }.onSuccess {
                statusText = "saved"
                loadPrefs()
            }.onFailure { statusText = "save error: ${it.message}" }
        }.start()
    }

    LaunchedEffect(Unit) {
        loadStreamers()
        loadPrefs()
        loadEvents()
    }

    MaterialTheme {
        Scaffold(topBar = { TopAppBar(title = { Text("StreamerNotify Android MVP") }) }) { padding ->
            Column(
                modifier = Modifier.fillMaxSize().padding(padding).padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text("API: $apiBase")
                Text("status: $statusText")

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = userIdInput, onValueChange = { userIdInput = it }, label = { Text("User ID") })
                    Button(onClick = { loadStreamers(); loadPrefs(); loadEvents() }) { Text("再読込") }
                }

                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("通知設定を追加/更新", style = MaterialTheme.typography.titleMedium)
                        OutlinedTextField(value = prefStreamerId, onValueChange = { prefStreamerId = it }, label = { Text("Streamer ID") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(value = prefPlatform, onValueChange = { prefPlatform = it }, label = { Text("Platform (youtube/twitch/x)") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(value = prefEventType, onValueChange = { prefEventType = it }, label = { Text("Event Type") }, modifier = Modifier.fillMaxWidth())
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = prefEnabled, onCheckedChange = { prefEnabled = it })
                            Text("Enabled")
                        }
                        Button(onClick = { savePref() }) { Text("保存") }
                    }
                }

                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("タイムラインフィルタ", style = MaterialTheme.typography.titleMedium)
                        OutlinedTextField(value = eventSourceFilter, onValueChange = { eventSourceFilter = it }, label = { Text("source (blank/youtube/twitch/x)") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(value = eventLimit, onValueChange = { eventLimit = it }, label = { Text("limit") }, modifier = Modifier.fillMaxWidth())
                        Button(onClick = { loadEvents() }) { Text("タイムライン再読込") }
                    }
                }

                Text("通知設定一覧", style = MaterialTheme.typography.titleMedium)
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
                    items(prefs) { p ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text("streamer=${p.streamerId} ${p.platform}/${p.eventType}")
                                Text(if (p.enabled) "ON" else "OFF")
                            }
                        }
                    }
                }

                Text("タイムライン", style = MaterialTheme.typography.titleMedium)
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
                    items(events) { e ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text("[${e.source}] ${e.eventType}")
                                Text("streamer=${e.streamerId} at ${e.occurredAt}")
                                if (e.payload.isNotBlank()) Text(e.payload)
                            }
                        }
                    }
                }
            }
        }
    }
}
