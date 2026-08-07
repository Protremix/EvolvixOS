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
 * EVM Contract Interaction Fragment
 *
 * Allows users to:
 * - View deployed EVM contracts
 * - Call contract functions (read-only)
 * - Deploy contracts from templates
 * - View contract events
 *
 * Uses native Android widgets only (no WebView, no external UI libs)
 * per Verdis dependency-free architecture requirement.
 */
class EvmFragment : Fragment() {

    private lateinit var api: VerdisApi
    private lateinit var contractList: LinearLayout
    private lateinit var templateList: LinearLayout
    private lateinit var statusText: TextView

    private val templates = listOf(
        ContractTemplate("ERC-20 Token", "Standard fungible token with mint/burn", "ERC20Token.sol"),
        ContractTemplate("Carbon Credit", "Carbon credit issuance & retirement (ERC-1155)", "CarbonCredit.sol"),
        ContractTemplate("Green Validator", "Green validator scoring registry", "GreenValidator.sol")
    )

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        // Native layout — no XML inflation, built programmatically
        val scrollView = ScrollView(requireContext())
        val container2 = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        // Title
        container2.addView(TextView(requireContext()).apply {
            text = "⚡ EVM Contracts"
            textSize = 24f
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(0, 0, 0, 24)
        })

        // Chain info
        statusText = TextView(requireContext()).apply {
            text = "Chain ID: 909 | Gas: 1 Gwei VRDX"
            textSize = 12f
            setTextColor(0xFF888888.toInt())
            setPadding(0, 0, 0, 16)
        }
        container2.addView(statusText)

        // Section: Deployed Contracts
        container2.addView(TextView(requireContext()).apply {
            text = "Deployed Contracts"
            textSize = 16f
            setTextColor(0xFF4F46E5.toInt())
            setPadding(0, 16, 0, 8)
        })

        contractList = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
        }
        container2.addView(contractList)

        // Section: Templates
        container2.addView(TextView(requireContext()).apply {
            text = "Contract Templates"
            textSize = 16f
            setTextColor(0xFF4F46E5.toInt())
            setPadding(0, 24, 0, 8)
        })

        templateList = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
        }

        templates.forEach { template ->
            val card = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(24, 16, 24, 16)
                setBackgroundColor(0xFF1A1A1E.toInt())
            }

            card.addView(TextView(requireContext()).apply {
                text = template.name
                textSize = 14f
                setTextColor(0xFFFFFFFF.toInt())
            })
            card.addView(TextView(requireContext()).apply {
                text = template.description
                textSize = 11f
                setTextColor(0xFF888888.toInt())
                setPadding(0, 4, 0, 0)
            })

            val deployBtn = Button(requireContext()).apply {
                text = "Deploy"
                setBackgroundColor(0xFF4F46E5.toInt())
                setTextColor(0xFFFFFFFF.toInt())
                setOnClickListener { onDeployClicked(template) }
            }
            card.addView(deployBtn)

            // Margin
            val params = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            params.setMargins(0, 0, 0, 12)
            card.layoutParams = params

            templateList.addView(card)
        }

        container2.addView(templateList)

        // Section: Gas Info
        container2.addView(TextView(requireContext()).apply {
            text = "Gas Costs (at 1 Gwei)"
            textSize = 16f
            setTextColor(0xFF4F46E5.toInt())
            setPadding(0, 24, 0, 8)
        })

        val gasInfo = """
            Simple Transfer: 21,000 gas (0.000021 VRDX)
            ERC-20 Transfer: 51,000 gas (0.000051 VRDX)
            Contract Deploy: 1,000,000+ gas (0.001+ VRDX)
            Carbon Credit Issue: 150,000 gas (0.00015 VRDX)
            Validator Score: 80,000 gas (0.00008 VRDX)
            
            Block Gas Limit: 30,000,000
            Max Contract Size: 24,576 bytes (EIP-170)
            EIP-1559: Dynamic base fee enabled
        """.trimIndent()

        container2.addView(TextView(requireContext()).apply {
            text = gasInfo
            textSize = 11f
            setTextColor(0xFF888888.toInt())
            setPadding(16, 8, 16, 16)
            setBackgroundColor(0xFF1A1A1E.toInt())
        })

        scrollView.addView(container2)
        return scrollView
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        api = VerdisApi()
        loadContracts()
    }

    private fun loadContracts() {
        lifecycleScope.launch {
            try {
                val response = withContext(Dispatchers.IO) { api.getEvmContracts() }
                contractList.removeAllViews()

                if (response.isNullOrEmpty()) {
                    contractList.addView(TextView(requireContext()).apply {
                        text = "No contracts deployed yet"
                        textSize = 12f
                        setTextColor(0xFF888888.toInt())
                    })
                } else {
                    response.forEach { contract ->
                        val card = LinearLayout(requireContext()).apply {
                            orientation = LinearLayout.VERTICAL
                            setPadding(24, 16, 24, 16)
                            setBackgroundColor(0xFF1A1A1E.toInt())
                        }
                        card.addView(TextView(requireContext()).apply {
                            text = contract.name
                            textSize = 14f
                            setTextColor(0xFFFFFFFF.toInt())
                        })
                        card.addView(TextView(requireContext()).apply {
                            text = contract.address
                            textSize = 10f
                            setTextColor(0xFF888888.toInt())
                            setPadding(0, 4, 0, 0)
                        })
                        contractList.addView(card)
                    }
                }
            } catch (e: Exception) {
                contractList.addView(TextView(requireContext()).apply {
                    text = "Cannot reach Verdis RPC"
                    textSize = 12f
                    setTextColor(0xFFEF4444.toInt())
                })
            }
        }
    }

    private fun onDeployClicked(template: ContractTemplate) {
        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    api.deployEvmContract(template.file)
                }
                Toast.makeText(
                    requireContext(),
                    "Deploying ${template.name}...",
                    Toast.LENGTH_SHORT
                ).show()
                loadContracts()
            } catch (e: Exception) {
                Toast.makeText(
                    requireContext(),
                    "Deploy failed: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    data class ContractTemplate(
        val name: String,
        val description: String,
        val file: String
    )

    data class DeployedContract(
        val name: String,
        val address: String
    )
}
