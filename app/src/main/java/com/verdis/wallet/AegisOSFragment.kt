package com.verdis.wallet

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * AegisOS Integration Fragment
 *
 * Shows:
 * - AegisOS system health
 * - AI agent status (11 agents)
 * - Active pipelines
 * - Verdis project management status
 *
 * Uses native widgets only per Verdis architecture requirement.
 */
class AegisOSFragment : Fragment() {

    private lateinit var api: VerdisApi
    private lateinit var agentList: LinearLayout
    private lateinit var pipelineList: LinearLayout
    private lateinit var healthText: TextView

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        val scrollView = ScrollView(requireContext())
        val container2 = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        // Title
        container2.addView(TextView(requireContext()).apply {
            text = "🛡️ AegisOS"
            textSize = 24f
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(0, 0, 0, 8)
        })

        container2.addView(TextView(requireContext()).apply {
            text = "AI Engineering Platform"
            textSize = 12f
            setTextColor(0xFF888888.toInt())
            setPadding(0, 0, 0, 16)
        })

        // Health status
        healthText = TextView(requireContext()).apply {
            text = "Checking AegisOS status..."
            textSize = 14f
            setTextColor(0xFF888888.toInt())
            setPadding(16, 12, 16, 12)
            setBackgroundColor(0xFF1A1A1E.toInt())
        }
        container2.addView(healthText)

        // Stats grid (2 columns)
        val statsGrid = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 12, 0, 12)
        }

        // Left column
        val leftCol = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        leftCol.addView(createStatCard("Agents", "11", 0xFF4F46E5.toInt()))
        leftCol.addView(createStatCard("Pipelines", "Active", 0xFF22C55E.toInt()))
        statsGrid.addView(leftCol)

        // Right column
        val rightCol = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        rightCol.addView(createStatCard("Tests", "1022", 0xFF4F46E5.toInt()))
        rightCol.addView(createStatCard("Endpoints", "283", 0xFF4F46E5.toInt()))
        statsGrid.addView(rightCol)

        container2.addView(statsGrid)

        // AI Agents section
        container2.addView(TextView(requireContext()).apply {
            text = "AI Agents"
            textSize = 16f
            setTextColor(0xFF4F46E5.toInt())
            setPadding(0, 16, 0, 8)
        })

        agentList = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
        }

        val agents = listOf(
            "CTO Agent" to "Architecture & strategy",
            "Architect Agent" to "System design",
            "Security Agent" to "Vulnerability scanning",
            "QA Agent" to "Quality assurance",
            "Planner Agent" to "Task decomposition",
            "Reviewer Agent" to "Code review",
            "Docs Agent" to "Documentation",
            "Memory Agent" to "Context retention",
            "Test Generator" to "Test suite generation",
            "CI Healer" to "CI/CD failure repair",
            "Verdis Enhancer" to "Verdis context injection"
        )

        agents.forEach { (name, desc) ->
            val card = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(20, 14, 20, 14)
                setBackgroundColor(0xFF1A1A1E.toInt())
            }

            val info = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.VERTICAL
                layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
            }
            info.addView(TextView(requireContext()).apply {
                text = name
                textSize = 13f
                setTextColor(0xFFFFFFFF.toInt())
            })
            info.addView(TextView(requireContext()).apply {
                text = desc
                textSize = 10f
                setTextColor(0xFF888888.toInt())
                setPadding(0, 2, 0, 0)
            })
            card.addView(info)

            // Status indicator
            card.addView(TextView(requireContext()).apply {
                text = "●"
                textSize = 12f
                setTextColor(0xFF22C55E.toInt())
            })

            val params = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            params.setMargins(0, 0, 0, 8)
            card.layoutParams = params

            agentList.addView(card)
        }

        container2.addView(agentList)

        // Active Pipelines section
        container2.addView(TextView(requireContext()).apply {
            text = "Active Pipelines"
            textSize = 16f
            setTextColor(0xFF4F46E5.toInt())
            setPadding(0, 16, 0, 8)
        })

        pipelineList = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
        }
        container2.addView(pipelineList)

        // Verdis project card
        container2.addView(TextView(requireContext()).apply {
            text = "Managed Project"
            textSize = 16f
            setTextColor(0xFF4F46E5.toInt())
            setPadding(0, 16, 0, 8)
        })

        val projectCard = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(20, 16, 20, 16)
            setBackgroundColor(0xFF1A1A1E.toInt())
        }
        projectCard.addView(TextView(requireContext()).apply {
            text = "Verdis Blockchain"
            textSize = 14f
            setTextColor(0xFFFFFFFF.toInt())
        })
        projectCard.addView(TextView(requireContext()).apply {
            text = "Type: blockchain | Status: Active | Health: Healthy"
            textSize = 11f
            setTextColor(0xFF22C55E.toInt())
            setPadding(0, 4, 0, 0)
        })
        projectCard.addView(TextView(requireContext()).apply {
            text = "13 pallets | 14 validators | 133 tests | EVM enabled"
            textSize = 10f
            setTextColor(0xFF888888.toInt())
            setPadding(0, 4, 0, 0)
        })
        container2.addView(projectCard)

        scrollView.addView(container2)
        return scrollView
    }

    private fun createStatCard(label: String, value: String, color: Int): View {
        val card = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(20, 16, 20, 16)
            setBackgroundColor(0xFF1A1A1E.toInt())
        }
        card.addView(TextView(requireContext()).apply {
            text = label
            textSize = 10f
            setTextColor(0xFF888888.toInt())
        })
        card.addView(TextView(requireContext()).apply {
            text = value
            textSize = 18f
            setTextColor(color)
            setPadding(0, 4, 0, 0)
        })
        val params = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        )
        params.setMargins(4, 4, 4, 4)
        card.layoutParams = params
        return card
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        api = VerdisApi()
        loadAegisOSStatus()
    }

    private fun loadAegisOSStatus() {
        lifecycleScope.launch {
            try {
                val health = withContext(Dispatchers.IO) { api.getAegisOSHealth() }
                healthText.text = "✅ AegisOS: ${health.status} | ${health.agents} agents active"
                healthText.setTextColor(0xFF22C55E.toInt())
            } catch (e: Exception) {
                healthText.text = "⚠️ AegisOS offline (not deployed yet)"
                healthText.setTextColor(0xFF888888.toInt())
            }
        }
    }
}
