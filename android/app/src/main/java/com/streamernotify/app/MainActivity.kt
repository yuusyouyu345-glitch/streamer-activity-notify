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
import androidx.compose.ui.unit.dp
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AppRoot() }
    }
}

data class StreamerItem(val id: Long, val displayName: String)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppRoot() {
    val apiBase = BuildConfig.API_BASE_URL
    val streamers = remember { mutableStateListOf<StreamerItem>() }
    var userIdInput by remember { mutableStateOf("1") }
    var statusText by remember { mutableStateOf("ready") }

    fun loadStreamers() {
        statusText = "loading..."
        Thread {
            runCatching {
                val req = Request.Builder().url("$apiBase/streamers").build()
                val body = OkHttpClient().newCall(req).execute().body?.string().orEmpty()
                val arr = JSONArray(body)
                val items = mutableListOf<StreamerItem>()
                for (i in 0 until arr.length()) {
                    val o = arr.getJSONObject(i)
                    items.add(StreamerItem(o.getLong("id"), o.getString("display_name")))
                }
                items
            }.onSuccess { items ->
                streamers.clear(); streamers.addAll(items)
                statusText = "loaded ${items.size} streamers"
            }.onFailure {
                statusText = "error: ${it.message}"
            }
        }.start()
    }

    LaunchedEffect(Unit) { loadStreamers() }

    MaterialTheme {
        Scaffold(
            topBar = { TopAppBar(title = { Text("StreamerNotify Android MVP") }) }
        ) { padding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(12.dp),
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
                    Button(onClick = { loadStreamers() }) { Text("再読込") }
                }
                Text("配信者一覧", style = MaterialTheme.typography.titleMedium)
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(streamers) { s ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text("#${s.id} ${s.displayName}")
                                Text("通知設定UIは次フェーズで詳細実装", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }
    }
}
