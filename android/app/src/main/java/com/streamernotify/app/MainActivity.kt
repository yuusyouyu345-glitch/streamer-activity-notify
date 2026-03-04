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
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
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
data class PrefItem(
    val streamerId: Long,
    val platform: String,
    val eventType: String,
    val enabled: Boolean,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppRoot() {
    val apiBase = BuildConfig.API_BASE_URL
    val streamers = remember { mutableStateListOf<StreamerItem>() }
    val prefs = remember { mutableStateListOf<PrefItem>() }

    var userIdInput by remember { mutableStateOf("1") }
    var statusText by remember { mutableStateOf("ready") }

    var prefStreamerId by remember { mutableStateOf("") }
    var prefPlatform by remember { mutableStateOf("youtube") }
    var prefEventType by remember { mutableStateOf("video_published") }
    var prefEnabled by remember { mutableStateOf(true) }

    val client = remember { OkHttpClient() }

    fun loadStreamers() {
        statusText = "loading streamers..."
        Thread {
            runCatching {
                val req = Request.Builder().url("$apiBase/streamers").build()
                val body = client.newCall(req).execute().body?.string().orEmpty()
                val arr = JSONArray(body)
                val items = mutableListOf<StreamerItem>()
                for (i in 0 until arr.length()) {
                    val o = arr.getJSONObject(i)
                    items.add(StreamerItem(o.getLong("id"), o.getString("display_name")))
                }
                items
            }.onSuccess { items ->
                streamers.clear(); streamers.addAll(items)
                if (prefStreamerId.isBlank() && items.isNotEmpty()) prefStreamerId = items.first().id.toString()
                statusText = "loaded ${items.size} streamers"
            }.onFailure {
                statusText = "streamers error: ${it.message}"
            }
        }.start()
    }

    fun loadPrefs() {
        val userId = userIdInput.ifBlank { "1" }
        statusText = "loading prefs..."
        Thread {
            runCatching {
                val req = Request.Builder().url("$apiBase/notification-preferences?user_id=$userId").build()
                val body = client.newCall(req).execute().body?.string().orEmpty()
                val arr = JSONArray(body)
                val items = mutableListOf<PrefItem>()
                for (i in 0 until arr.length()) {
                    val o = arr.getJSONObject(i)
                    items.add(
                        PrefItem(
                            streamerId = o.getLong("streamer_id"),
                            platform = o.getString("platform"),
                            eventType = o.getString("event_type"),
                            enabled = o.getBoolean("enabled"),
                        )
                    )
                }
                items
            }.onSuccess { items ->
                prefs.clear(); prefs.addAll(items)
                statusText = "loaded ${items.size} prefs"
            }.onFailure {
                statusText = "prefs error: ${it.message}"
            }
        }.start()
    }

    fun savePref() {
        val userId = userIdInput.toLongOrNull() ?: 1L
        val streamerId = prefStreamerId.toLongOrNull()
        if (streamerId == null) {
            statusText = "streamer id invalid"
            return
        }

        statusText = "saving pref..."
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
                client.newCall(req).execute().use { res ->
                    if (!res.isSuccessful) error("save failed: ${res.code}")
                }
            }.onSuccess {
                statusText = "saved"
                loadPrefs()
            }.onFailure {
                statusText = "save error: ${it.message}"
            }
        }.start()
    }

    LaunchedEffect(Unit) {
        loadStreamers()
        loadPrefs()
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
                    OutlinedTextField(
                        value = userIdInput,
                        onValueChange = { userIdInput = it },
                        label = { Text("User ID") }
                    )
                    Button(onClick = { loadStreamers(); loadPrefs() }) { Text("再読込") }
                }

                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("通知設定を追加/更新", style = MaterialTheme.typography.titleMedium)
                        OutlinedTextField(
                            value = prefStreamerId,
                            onValueChange = { prefStreamerId = it },
                            label = { Text("Streamer ID") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        OutlinedTextField(
                            value = prefPlatform,
                            onValueChange = { prefPlatform = it },
                            label = { Text("Platform (youtube/twitch/x)") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        OutlinedTextField(
                            value = prefEventType,
                            onValueChange = { prefEventType = it },
                            label = { Text("Event Type") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = prefEnabled, onCheckedChange = { prefEnabled = it })
                            Text("Enabled")
                        }
                        Button(onClick = { savePref() }) { Text("保存") }
                    }
                }

                Text("配信者一覧", style = MaterialTheme.typography.titleMedium)
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
                    items(streamers) { s ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Text("#${s.id} ${s.displayName}", modifier = Modifier.padding(12.dp))
                        }
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
            }
        }
    }
}
