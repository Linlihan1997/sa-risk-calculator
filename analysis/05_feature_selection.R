# Step 05. Feature selection in the training set: LASSO logistic regression (10-fold CV, lambda.1se) and Boruta
# (100 iterations). Predictors selected by both methods form the final set; multicollinearity is checked with VIF.
# Usage (from the analysis/ folder): Rscript 05_feature_selection.R
# Outputs in results/feature_selection/: LASSO coefficients, Boruta statistics, selection summary,
# VIF of the final predictors, and data/derived/vars_selected.csv (final predictors).
suppressPackageStartupMessages({ library(glmnet); library(Boruta); library(car) })
root <- Sys.getenv("YRBS_SA_ROOT", ".")
inp <- file.path(root, "data", "derived", "train_70_imputed.csv")
dir.create(file.path(root, "results", "feature_selection"), recursive = TRUE, showWarnings = FALSE)
outp <- file.path(root, "results", "feature_selection", "train")
max_runs <- 100
set.seed(2026)

d <- read.csv(inp, fileEncoding = "UTF-8-BOM")
vars <- c("age","grade","female","raceeth","sexual_minority","bmi","sad_hopeless","plan","sleep_hours",
          "nicotine_status","alcohol_status","marijuana_status","other_drug_any","early_onset_any",
          "bullying_count","school_victim_any","fighting_any","weapon_any","sexual_dating_violence_any",
          "sexual_behavior","fv_none_count","no_breakfast","drank_soda","pa_5days","sports_pe_any",
          "concussion","dentist","hiv_std_test_any")
lab <- c(age="Age", grade="Grade", female="Female sex", raceeth="Race/ethnicity", sexual_minority="Sexual minority",
         bmi="BMI", sad_hopeless="Persistent sadness/hopelessness", plan="Suicide plan", sleep_hours="Sleep hours",
         nicotine_status="Tobacco/nicotine use", alcohol_status="Alcohol use", marijuana_status="Marijuana use",
         other_drug_any="Lifetime illicit drug use or prescription opioid misuse", early_onset_any="Substance use before 13",
         bullying_count="Bullying victimization", school_victim_any="School violence/unsafe",
         fighting_any="Physical fighting", weapon_any="Weapon carrying",
         sexual_dating_violence_any="Sexual/dating violence", sexual_behavior="Sexual behavior",
         fv_none_count="Fruit/vegetable categories not eaten", no_breakfast="No breakfast",
         drank_soda="Soda consumption", pa_5days="Physically active >=5 d/wk", sports_pe_any="Sports team or PE",
         concussion="Sports concussion", dentist="Dental visit", hiv_std_test_any="HIV/STD testing")
fac <- c("raceeth","nicotine_status","alcohol_status","marijuana_status","sexual_behavior")
d$raceeth <- relevel(factor(d$raceeth), ref = "White")
for (v in setdiff(fac, "raceeth")) d[[v]] <- factor(d[[v]], levels = 0:2)
y <- d$sa

# ---------- LASSO ----------
X <- model.matrix(~ ., data = d[, vars])[, -1]
assign_var <- attr(model.matrix(~ ., data = d[, vars]), "assign")[-1]
foldid <- sample(rep(1:10, length.out = nrow(X)))
cvfit <- cv.glmnet(X, y, family = "binomial", alpha = 1, nfolds = 10, foldid = foldid, type.measure = "deviance")
fit <- cvfit$glmnet.fit
pick <- function(s) {
  b <- as.matrix(coef(cvfit, s = s))[-1, 1]
  sel_cols <- names(b)[b != 0]
  list(vars = vars[sort(unique(assign_var[b != 0]))], coefs = b)
}
lmin <- pick("lambda.min"); l1se <- pick("lambda.1se")
coef_tab <- data.frame(term = colnames(X), variable = vars[assign_var],
                       coef_lambda_min = round(lmin$coefs, 4), coef_lambda_1se = round(l1se$coefs, 4))
write.csv(coef_tab, paste0(outp, "_lasso_coefficients.csv"), row.names = FALSE)

# ---------- Boruta ----------
bd <- d[, vars]
bor <- Boruta(x = bd, y = factor(y), maxRuns = max_runs, doTrace = 0, num.trees = 300, num.threads = 2)
saveRDS(bor, paste0(outp, "_boruta.rds"))
bstat <- attStats(bor)
bstat$variable <- rownames(bstat)
write.csv(bstat, paste0(outp, "_boruta_stats.csv"), row.names = FALSE)

# ---------- summary ----------
summ <- data.frame(variable = vars, label = unname(lab[vars]),
                   lasso_lambda_min = vars %in% lmin$vars, lasso_lambda_1se = vars %in% l1se$vars,
                   boruta = as.character(bstat[vars, "decision"]), boruta_meanImp = round(bstat[vars, "meanImp"], 2))
summ$lasso_1se_and_boruta_confirmed <- summ$lasso_lambda_1se & summ$boruta == "Confirmed"
write.csv(summ, paste0(outp, "_selection_summary.csv"), row.names = FALSE)
cat(sprintf("lambda.min=%.5f (%d vars)  lambda.1se=%.5f (%d vars)\n", cvfit$lambda.min, length(lmin$vars),
            cvfit$lambda.1se, length(l1se$vars)))
cat("Boruta:", paste(names(table(bstat$decision)), table(bstat$decision), collapse = "; "), "\n")

# ---------- final predictors: LASSO lambda.1se AND Boruta confirmed ----------
final_vars <- summ$variable[summ$lasso_1se_and_boruta_confirmed]
write.csv(data.frame(variable = final_vars, label = unname(lab[final_vars])),
          file.path(root, "data", "derived", "vars_selected.csv"), row.names = FALSE)
cat(length(final_vars), "predictors selected by both methods\n")

# ---------- VIF of the final predictors ----------
g <- glm(reformulate(final_vars, "sa"), data = d, family = binomial)
v <- car::vif(g)
if (is.matrix(v)) {
  vt <- data.frame(variable = rownames(v), GVIF = v[, 1], Df = v[, 2], adj_GVIF = v[, 3], VIF_equiv = v[, 3]^2)
} else vt <- data.frame(variable = names(v), GVIF = v, Df = 1, adj_GVIF = sqrt(v), VIF_equiv = v)
write.csv(vt, paste0(outp, "_vif_final.csv"), row.names = FALSE)
cat("max VIF-equivalent:", round(max(vt$VIF_equiv), 2), "\n")
